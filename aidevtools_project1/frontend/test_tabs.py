import flet as ft

def main(page: ft.Page):
    tabs_list = [
        ft.Tab(label="Tab 1"),
        ft.Tab(label="Tab 2"),
    ]
    tab_bar = ft.TabBar(tabs=tabs_list)
    
    body = ft.Text("Content 1")
    
    def on_change(e):
        body.value = f"Content {e.control.selected_index + 1}"
        page.update()
        
    t = ft.Tabs(
        content=tab_bar,
        length=len(tabs_list),
        selected_index=0,
        on_change=on_change
    )
    
    page.add(t, body)

if __name__ == "__main__":
    ft.app(main)
