import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
from backend.youtube_mcp import extract_video_id, main

def test_extract_video_id():
    """Test extracting video ID (same logic as youtube_api, but tested safely here)."""
    assert extract_video_id("https://www.youtube.com/watch?v=12345678901") == "12345678901"
    assert extract_video_id("12345678901") == "12345678901"

@pytest.mark.asyncio
async def test_main_print_usage():
    """Test main prints usage when no args provided."""
    with patch.object(sys, 'argv', ['youtube_mcp.py']):
        with patch('builtins.print') as mock_print:
            await main()
            # It prints usage logic if no relevant flags set
            mock_print.assert_called()
            # Usage might be printed multiple times or once
            found = False
            for call in mock_print.call_args_list:
                if call.args and "Usage:" in call.args[0]:
                    found = True
                    break
            assert found

@pytest.mark.asyncio
@patch('backend.youtube_mcp.stdio_client')
@patch('backend.youtube_mcp.ClientSession')
async def test_main_info(mock_session_cls, mock_stdio):
    """Test main with --info flag."""
    # Mock context managers
    mock_connection = AsyncMock()
    mock_stdio.return_value.__aenter__.return_value = (None, None)
    
    # Mock session
    mock_session = AsyncMock()
    mock_session_cls.return_value.__aenter__.return_value = mock_session
    
    # Mock tool call result
    mock_result = MagicMock()
    mock_result.content = [MagicMock(text="Video Info")]
    mock_session.call_tool.return_value = mock_result
    
    with patch.object(sys, 'argv', ['youtube_mcp.py', '--info']):
        with patch('builtins.print') as mock_print:
            await main()
            
            mock_session.initialize.assert_awaited_once()
            # Default ID uses default url
            mock_session.call_tool.assert_awaited_with("get_video_info", arguments={"url": "https://www.youtube.com/watch?v=EMd3H0pNvSE"})
            
            # Verify it printed the info
            printed_args = [call[0][0] for call in mock_print.call_args_list if call.args]
            assert "Video Info" in printed_args

@pytest.mark.asyncio
@patch('backend.youtube_mcp.stdio_client')
@patch('backend.youtube_mcp.ClientSession')
async def test_main_transcript_upload(mock_session_cls, mock_stdio):
    """Test main with --transcript and --upload flags."""
    mock_stdio.return_value.__aenter__.return_value = (None, None)
    mock_session = AsyncMock()
    mock_session_cls.return_value.__aenter__.return_value = mock_session
    
    mock_result = MagicMock()
    mock_result.content = [MagicMock(text="Transcript Content")]
    mock_session.call_tool.return_value = mock_result
    
    # Mock load_data and database via sys.modules
    with patch.dict(sys.modules, {
        'load_data': MagicMock(),
        'database': MagicMock()
    }), \
    patch('backend.load_data.update_transcript_text') as mock_update:
        
        # Test with specific ID
        args = ['youtube_mcp.py', '12345678901', '--transcript', '--upload']
        with patch.object(sys, 'argv', args):
            await main()
            
            mock_session.call_tool.assert_awaited_with("get_transcript", arguments={"url": "https://www.youtube.com/watch?v=12345678901"})
            
            # Verify init_db from mocked database module was called
            sys.modules['database'].init_db.assert_called_once()
            
            # Verify load_data.update_transcript_text was called
            sys.modules['load_data'].update_transcript_text.assert_called_once()
