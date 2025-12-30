import sys
import unittest
from unittest.mock import patch, MagicMock

# Mock modules before importing youtube_api if possible, 
# or allow youtube_api to import them but patch the resulting objects.
# Since the imports are local to the 'if args.upload' block, we can patch sys.modules.

class TestYoutubeApiUpload(unittest.TestCase):
    @patch('youtube_api.list_transcripts_json')
    @patch('youtube_api.extract_video_id')
    def test_upload_flow(self, mock_extract, mock_list):
        # Setup mocks
        mock_extract.return_value = "TEST_ID"
        mock_list.return_value = {
            "video_id": "TEST_ID",
            "transcripts": []
        }
        
        # Mocking load_data and database
        mock_load_data = MagicMock()
        mock_database = MagicMock()
        mock_session = MagicMock()
        mock_database.get_session.return_value = mock_session
        
        with patch.dict(sys.modules, {'load_data': mock_load_data, 'database': mock_database}):
            # We import youtube_api here to ensure patches work if it was top-level, 
            # but for local imports, sys.modules patch is key.
            import youtube_api
            
            # Simulate command line arguments
            test_args = ['youtube_api.py', 'TEST_ID', '--upload']
            with patch.object(sys, 'argv', test_args):
                youtube_api.main()
            
            # Verify calls
            mock_database.init_db.assert_called_once()
            mock_database.get_session.assert_called_once()
            mock_load_data.load_video_metadata.assert_called_once()
            mock_load_data.load_transcripts_metadata.assert_called_once()
            mock_session.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()