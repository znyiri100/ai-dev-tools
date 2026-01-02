import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from frontend_nicegui.api_client import ApiClient

class AsyncIterator:
    def __init__(self, items):
        self.items = iter(items)
    def __aiter__(self):
        return self
    async def __anext__(self):
        try:
            return next(self.items)
        except StopIteration:
            raise StopAsyncIteration

@pytest.mark.asyncio
async def test_get_video_success():
    """Test get_video successfully call."""
    client = ApiClient()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "123"}
    
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        response = await client.get_video("123")
        assert response.status_code == 200
        mock_get.assert_called_once()
        # Verify URL construction and params
        args, kwargs = mock_get.call_args
        assert "/api/v1/video/123" in args[0]
        assert kwargs["params"] == {"include_transcript": "true"}

@pytest.mark.asyncio
async def test_store_video():
    """Test store_video call."""
    client = ApiClient()
    mock_response = MagicMock()
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        await client.store_video("123")
        mock_post.assert_called_once()
        args, _ = mock_post.call_args
        assert "/api/v1/video/123/store" in args[0]

@pytest.mark.asyncio
async def test_generate_study_guide():
    """Test generate_study_guide with prompt."""
    client = ApiClient()
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        await client.generate_study_guide("123", "en", prompt="Custom Prompt")
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        assert kwargs["json"] == {"prompt": "Custom Prompt"}

@pytest.mark.asyncio
async def test_chat_with_guide_stream():
    """Test chat_with_guide_stream generator."""
    client = ApiClient()
    
    # Mock the stream context manager
    mock_response = MagicMock()
    mock_response.aiter_text.return_value = AsyncIterator(["Hello", " World"])
    
    mock_stream_cm = AsyncMock()
    mock_stream_cm.__aenter__.return_value = mock_response
    
    with patch("httpx.AsyncClient.stream", return_value=mock_stream_cm) as mock_stream:
        chunks = []
        async for chunk in client.chat_with_guide_stream("123", "en", "Full Message", []):
            chunks.append(chunk)
            
        assert chunks == ["Hello", " World"]
        mock_stream.assert_called_once()
