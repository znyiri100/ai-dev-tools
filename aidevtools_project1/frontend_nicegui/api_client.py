import httpx
import os
import json

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

class ApiClient:
    def __init__(self):
        self.base_url = API_BASE
        self.headers = {"Content-Type": "application/json"}

    async def _get(self, endpoint, params=None):
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.get(f"{self.base_url}{endpoint}", params=params)
                return response
            except Exception as e:
                print(f"Error GET {endpoint}: {e}")
                return None

    async def _post(self, endpoint, json_data=None, params=None):
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(f"{self.base_url}{endpoint}", json=json_data, params=params)
                return response
            except Exception as e:
                print(f"Error POST {endpoint}: {e}")
                return None

    async def _put(self, endpoint, json_data=None, params=None):
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.put(f"{self.base_url}{endpoint}", json=json_data, params=params)
                return response
            except Exception as e:
                print(f"Error PUT {endpoint}: {e}")
                return None


    async def get_video(self, video_id, include_transcript=True):
        params = {"include_transcript": str(include_transcript).lower()}
        return await self._get(f"/api/v1/video/{video_id}", params=params)

    async def store_video(self, video_id):
        return await self._post(f"/api/v1/video/{video_id}/store")

    async def list_videos(self):
        return await self._get("/api/v1/db/videos")

    async def get_video_details(self, video_id):
        return await self._get(f"/api/v1/db/video/{video_id}")

    async def generate_study_guide(self, video_id, lang_code, prompt=None):
        payload = {"prompt": prompt} if prompt else None
        return await self._post(f"/api/v1/transcript/{video_id}/{lang_code}/generate_study_guide", json_data=payload)

    async def generate_quiz(self, video_id, lang_code, prompt=None):
        payload = {"prompt": prompt} if prompt else None
        return await self._post(f"/api/v1/transcript/{video_id}/{lang_code}/generate_quiz", json_data=payload)

    async def chat_with_guide(self, video_id, lang_code, message, history):
        payload = {"message": message, "history": history}
        return await self._post(f"/api/v1/transcript/{video_id}/{lang_code}/chat", json_data=payload)
    
    async def update_transcript_content(self, video_id, lang_code, study_guide=None, quiz=None):
        payload = {}
        if study_guide is not None:
            payload["study_guide"] = study_guide
        if quiz is not None:
            payload["quiz"] = quiz
        return await self._put(f"/api/v1/transcript/{video_id}/{lang_code}/update", json_data=payload)
    
    # Reusing yt-dlp logic would be ideal if we can share code, 
    # but for now we'll keep the client focused on the API server.
    # The Gradio app imported youtube_api directly. 
    # We should copy that file or refactor. 
    # For now, let's assume we copy youtube_api.py to frontend_nicegui.

