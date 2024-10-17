import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
from encryption import generate_key, load_key, encrypt_file, decrypt_file
from cryptography.fernet import Fernet
from config import Config

class TestEncryptionFunctions(unittest.TestCase):
    @patch('encryption.os.makedirs')
    @patch('encryption.open', new_callable=mock_open)
    @patch('encryption.logger.info')
    def test_generate_key(self, mock_logger, mock_file, mock_makedirs):
        # Mock the directory creation and file operations
        mock_makedirs.return_value = None
        mock_file().write = MagicMock()

        key = generate_key()
        # Verify key is generated correctly
        self.assertTrue(isinstance(key, bytes))
        self.assertTrue(len(key) > 0)

        # Check that the key was written to the correct file
        mock_makedirs.assert_called_once_with(os.path.dirname(Config.AES_KEY_FILE), exist_ok=True)
        mock_file.assert_any_call(Config.AES_KEY_FILE, 'wb')  # Changed to assert_any_call
        mock_file().write.assert_called_once_with(key)

        # Ensure log message was created
        mock_logger.assert_called_with('AES encryption key generated.')

    @patch('encryption.os.path.exists')
    @patch('encryption.open', new_callable=mock_open, read_data=b'test-key')
    @patch('encryption.generate_key')
    def test_load_key_existing(self, mock_generate_key, mock_file, mock_exists):
        # Simulate key file already exists
        mock_exists.return_value = True

        key = load_key()

        # Ensure it reads the existing key file
        mock_file.assert_called_once_with(Config.AES_KEY_FILE, 'rb')
        self.assertEqual(key, b'test-key')

        # Ensure `generate_key` is not called
        mock_generate_key.assert_not_called()

    @patch('encryption.os.path.exists')
    @patch('encryption.generate_key')
    def test_load_key_generate(self, mock_generate_key, mock_exists):
        # Simulate key file does not exist
        mock_exists.return_value = False
        mock_generate_key.return_value = b'new-generated-key'

        key = load_key()

        # Ensure a new key is generated
        mock_generate_key.assert_called_once()
        self.assertEqual(key, b'new-generated-key')

    @patch('encryption.load_key', return_value=Fernet.generate_key())
    @patch('encryption.open', new_callable=mock_open)
    @patch('encryption.logger.info')
    def test_encrypt_file(self, mock_logger, mock_file, mock_load_key):
        # Prepare test data
        mock_file().read = MagicMock(return_value=b'some data')
        mock_file().write = MagicMock()

        test_file_path = 'testfile.txt'

        # Encrypt the file
        encrypt_file(test_file_path)

        # Ensure the file is read, then written back in encrypted form
        mock_file.assert_any_call(test_file_path, 'rb')
        mock_file.assert_any_call(test_file_path, 'wb')
        mock_logger.assert_called_with(f'File encrypted: {test_file_path}')

    @patch('encryption.load_key', return_value=Fernet.generate_key())
    @patch('encryption.open', new_callable=mock_open)
    @patch('encryption.logger.info')
    def test_decrypt_file(self, mock_logger, mock_file, mock_load_key):
        # Generate a key and create a Fernet instance to encrypt and decrypt correctly
        key = mock_load_key.return_value
        fernet = Fernet(key)

        # Prepare encrypted data to simulate a file
   
