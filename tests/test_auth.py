import unittest
from unittest.mock import patch, MagicMock, mock_open
from auth import (
    get_github_username, authenticate, get_access_token, save_token,
    set_active_user, load_active_user, load_token, is_authenticated, get_current_user
)
from datetime import datetime, timedelta, timezone
import os
from config import Config

class TestAuthFunctions(unittest.TestCase):

    @patch('auth.requests.get')
    def test_get_github_username(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {'login': 'testuser'}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        username = get_github_username('dummy_token')
        self.assertEqual(username, 'testuser')
        mock_get.assert_called_once_with(Config.API_URL, headers={'Authorization': 'token dummy_token'})

    @patch('auth.webbrowser.open')
    @patch('auth.HTTPServer')
    @patch('auth.get_access_token', return_value='dummy_token')
    @patch('auth.get_github_username', return_value='testuser')
    @patch('auth.save_token')
    @patch('auth.set_active_user')
    def test_authenticate_success(self, mock_set_active_user, mock_save_token, mock_get_username, mock_get_token, mock_server, mock_webbrowser):
        # Mock server behavior and simulate successful authentication
        mock_instance = MagicMock()
        mock_instance.auth_code = 'auth_code'
        mock_instance.auth_state = 'aaaaaaaaaaaaaaaa'  # Ensure this matches the generated state in the test
        mock_server.return_value = mock_instance

        # Ensure the state generated in the function matches the mock
        with patch('auth.secrets.choice', return_value='a'):
            token = authenticate()

        # Verify the token is correctly returned
        self.assertEqual(token, 'dummy_token')
        mock_webbrowser.assert_called_once()
        mock_get_token.assert_called_once_with('auth_code')
        mock_get_username.assert_called_once_with('dummy_token')
        mock_save_token.assert_called_once_with('dummy_token', 'testuser')
        mock_set_active_user.assert_called_once_with('testuser')
        
    @patch('auth.requests.post')
    def test_get_access_token(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {'access_token': 'dummy_access_token'}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        token = get_access_token('dummy_code')
        self.assertEqual(token, 'dummy_access_token')
        mock_post.assert_called_once()

    @patch('auth.os.makedirs')
    @patch('auth.open', new_callable=mock_open)
    @patch('auth.logger.info')
    def test_save_token(self, mock_logger, mock_file, mock_makedirs):
        save_token('dummy_token', 'testuser')
        mock_makedirs.assert_called_once_with(os.path.join(Config.TOKENS_DIR), exist_ok=True)
        mock_file.assert_called_once_with(os.path.join(Config.TOKENS_DIR, 'testuser.env'), 'w')
        mock_logger.assert_called_once_with('Token saved for user testuser.')

    @patch('auth.open', new_callable=mock_open)
    @patch('auth.logger.info')
    def test_set_active_user(self, mock_logger, mock_file):
        set_active_user('testuser')
        mock_file.assert_called_once_with(Config.ACTIVE_USER_FILE, 'w')
        mock_logger.assert_called_once_with('Active user set to testuser.')

    @patch('auth.os.path.exists', return_value=True)
    @patch('auth.open', new_callable=mock_open, read_data='testuser')
    def test_load_active_user(self, mock_file, mock_exists):
        username = load_active_user()
        self.assertEqual(username, 'testuser')
        mock_exists.assert_called_once_with(Config.ACTIVE_USER_FILE)
        mock_file.assert_called_once_with(Config.ACTIVE_USER_FILE, 'r')

    @patch('auth.os.path.exists', return_value=False)
    def test_load_active_user_no_file(self, mock_exists):
        username = load_active_user()
        self.assertIsNone(username)
        mock_exists.assert_called_once_with(Config.ACTIVE_USER_FILE)

    @patch('auth.os.path.exists', return_value=True)
    @patch('auth.open', new_callable=mock_open, read_data='GITHUB_TOKEN=dummy_token\nAUTH_TIMESTAMP=2023-10-12T12:34:56+00:00')
    def test_load_token(self, mock_file, mock_exists):
        token, timestamp = load_token('testuser')
        self.assertEqual(token, 'dummy_token')
        self.assertEqual(timestamp, '2023-10-12T12:34:56+00:00')
        mock_exists.assert_called_once_with(os.path.join(Config.TOKENS_DIR, 'testuser.env'))
        mock_file.assert_called_once_with(os.path.join(Config.TOKENS_DIR, 'testuser.env'), 'r')

    @patch('auth.os.path.exists', return_value=False)
    def test_load_token_no_file(self, mock_exists):
        token_data = load_token('testuser')
        self.assertIsNone(token_data)
        mock_exists.assert_called_once_with(os.path.join(Config.TOKENS_DIR, 'testuser.env'))

    @patch('auth.datetime')
    @patch('auth.load_active_user', return_value='testuser')
    @patch('auth.load_token', return_value=('dummy_token', '2023-10-12T12:34:56+00:00'))
    @patch('auth.logger.info')
    def test_is_authenticated_success(self, mock_logger, mock_load_token, mock_load_active_user, mock_datetime):
        mock_datetime.now.return_value = datetime(2023, 10, 12, 12, 37, 56, tzinfo=timezone.utc)
        mock_datetime.fromisoformat.return_value = datetime(2023, 10, 12, 12, 34, 56, tzinfo=timezone.utc)
        result = is_authenticated()
        self.assertTrue(result)

    @patch('auth.datetime')
    @patch('auth.load_active_user', return_value='testuser')
    @patch('auth.load_token', return_value=('dummy_token', '2023-10-12T12:00:00+00:00'))
    @patch('auth.logger.info')
    def test_is_authenticated_expired(self, mock_logger, mock_load_token, mock_load_active_user, mock_datetime):
        mock_datetime.now.return_value = datetime(2023, 10, 12, 12, 10, 1, tzinfo=timezone.utc)
        mock_datetime.fromisoformat.return_value = datetime(2023, 10, 12, 12, 00, 00, tzinfo=timezone.utc)
        result = is_authenticated()
        self.assertFalse(result)
        mock_logger.assert_called_once_with('Authentication expired for user testuser.')

if __name__ == '__main__':
    unittest.main()
