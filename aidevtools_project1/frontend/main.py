import flet as ft
import httpx

API_BASE = "http://localhost:8000"

def main(page: ft.Page):
    page.title = "YouTube Transcript Manager"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 1000
    page.window.height = 800

    # --- SnackBar Helper ---
    snack_bar = ft.SnackBar(content=ft.Text(""))
    page.overlay.append(snack_bar)

    def show_message(text):
        snack_bar.content = ft.Text(text)
        snack_bar.open = True
        snack_bar.update()

    # --- Shared Logic ---
    def create_video_info_controls(data):
        meta = data.get("metadata", {})
        transcripts = data.get("transcripts", [])
        
        controls = []
        
        # Metadata Card
        controls.append(
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(meta.get("title", "No Title"), size=20, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Author: {meta.get('author', 'Unknown')} | Duration: {meta.get('duration', '?')} | Views: {meta.get('view_count', '?')}"),
                        ft.Text(meta.get("description", ""), size=12, italic=True, max_lines=3, overflow=ft.TextOverflow.ELLIPSIS),
                    ]),
                    padding=10
                )
            )
        )
        
        # Transcripts List Table
        t_rows = []
        for t in transcripts:
            t_rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(t.get("language", "?"))),
                    ft.DataCell(ft.Text(t.get("language_code", "?"))),
                    ft.DataCell(ft.Checkbox(value=t.get("is_generated", False), disabled=True)),
                ])
            )
            
        if t_rows:
            controls.append(
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Language")),
                        ft.DataColumn(ft.Text("Code")),
                        ft.DataColumn(ft.Text("Auto-Gen")),
                    ],
                    rows=t_rows
                )
            )
        else:
            controls.append(ft.Text("No transcripts found."))

        # Transcript Text Expanders
        has_text = False
        for t in transcripts:
            txt = t.get("transcript")
            if txt:
                has_text = True
                lang = t.get("language", "Unknown")
                controls.append(
                    ft.ExpansionTile(
                        title=ft.Text(f"Transcript: {lang}"),
                        controls=[
                            ft.Container(
                                content=ft.Text(txt, selectable=True),
                                padding=10,
                                height=300, 
                            )
                        ],
                        initially_expanded=False
                    )
                )
        
        if not has_text and transcripts:
            controls.append(ft.Text("Transcript text not fetched (or empty).", italic=True))

        return controls

    # --- UI Elements: Search Tab ---
    video_id_input = ft.TextField(label="Video ID or URL", width=400)
    transcript_check = ft.Checkbox(label="Include Transcript", value=True)
    
    info_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    
    def get_info_click(e):
        if not video_id_input.value:
            show_message("Please enter a Video ID")
            return
            
        try:
            vid = video_id_input.value
            include_t = str(transcript_check.value).lower()
            with httpx.Client() as client:
                resp = client.get(f"{API_BASE}/api/v1/video/{vid}", params={"include_transcript": include_t})
                if resp.status_code == 200:
                    data = resp.json()
                    info_container.controls.clear()
                    info_container.controls.extend(create_video_info_controls(data))
                    info_container.update()
                else:
                    show_message(f"Error: {resp.text}")
        except Exception as ex:
             show_message(f"Connection Error: {ex}")

    def store_db_click(e):
        if not video_id_input.value:
            show_message("Please enter a Video ID")
            return
        
        try:
            vid = video_id_input.value
            include_t = str(transcript_check.value).lower()
            with httpx.Client() as client:
                resp = client.post(f"{API_BASE}/api/v1/video/{vid}/store", params={"include_transcript": include_t})
                if resp.status_code == 200:
                    show_message("Success! Video and transcripts stored.")
                    refresh_db_list(None)
                else:
                    show_message(f"Error: {resp.text}")
        except Exception as ex:
             show_message(f"Connection Error: {ex}")

    search_tab = ft.Container(
        content=ft.Column([
            ft.Row([video_id_input, transcript_check, ft.FilledButton("Get Info", on_click=get_info_click), ft.FilledButton("Store in DB", on_click=store_db_click)]),
            ft.Divider(),
            info_container
        ], expand=True),
        padding=20
    )

    # --- UI Elements: Database Tab ---
    db_list = ft.ListView(expand=True, spacing=10)

    def show_db_detail(video_id):
        try:
            with httpx.Client() as client:
                resp = client.get(f"{API_BASE}/api/v1/db/video/{video_id}")
                if resp.status_code == 200:
                    data = resp.json()
                    dlg = ft.AlertDialog(
                        title=ft.Text("Video Details"),
                        content=ft.Container(
                            content=ft.Column(create_video_info_controls(data), scroll=ft.ScrollMode.AUTO),
                            width=800, height=600 
                        )
                    )
                    page.dialog = dlg
                    dlg.open = True
                    page.update()
                else:
                    show_message(f"Error: {resp.text}")
        except Exception as e:
            show_message(f"Error: {e}")

    def refresh_db_list(e):
        db_list.controls.clear()
        try:
            with httpx.Client() as client:
                resp = client.get(f"{API_BASE}/api/v1/db/videos")
                if resp.status_code == 200:
                    videos = resp.json()
                    for v in videos:
                        vid = v.get('video_id')
                        db_list.controls.append(
                            ft.Card(
                                content=ft.ListTile(
                                    leading=ft.Icon(ft.Icons.VIDEO_LIBRARY),
                                    title=ft.Text(v.get("title", "No Title")),
                                    subtitle=ft.Text(f"ID: {vid} | Fetched: {v.get('fetched_at')}"),
                                    on_click=lambda e, video_id=vid: show_db_detail(video_id)
                                )
                            )
                        )
                else:
                     db_list.controls.append(ft.Text(f"Error fetching DB: {resp.text}"))
        except Exception as ex:
            db_list.controls.append(ft.Text(f"Connection Error: {ex}"))
        page.update()

    db_tab = ft.Container(
        content=ft.Column([
            ft.FilledButton("Refresh List", on_click=refresh_db_list),
            db_list
        ]),
        padding=20
    )

    # --- Flet 0.80.0 Tabs Management ---
    all_tab_contents = [search_tab, db_tab]
    
    body = ft.Container(content=all_tab_contents[0], expand=True)

    def tabs_changed(e):
        body.content = all_tab_contents[e.control.selected_index]
        body.update()

    tabs_list = [
        ft.Tab(label="Search & Store", icon=ft.Icons.SEARCH),
        ft.Tab(label="Database Videos", icon=ft.Icons.VIDEO_LIBRARY),
    ]

    tab_bar = ft.TabBar(tabs=tabs_list)

    t = ft.Tabs(
        content=tab_bar,
        length=len(tabs_list),
        selected_index=0,
        on_change=tabs_changed,
        expand=False 
    )

    page.add(
        ft.Column([t, body], expand=True)
    )

if __name__ == "__main__":
    ft.app(main)