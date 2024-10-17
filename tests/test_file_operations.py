import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
from file_operations import upload, download, list_files, delete, sanitize_path
from encryption import encrypt_file, decrypt_file
from logger import logger

class TestFileOperations(unittest.TestCase):

    @patch('file_operations.os.path.isfile', return_value=True)
    @patch('file_operations.os.makedirs')
    @patch('file_operations.shutil.copy')
    @patch('file_operations.encrypt_file')
    @patch('file_operations.logger.info')
    def test_upload_success(self, mock_logger, mock_encrypt, mock_copy, mock_makedirs, mock_isfile):
        file_path = 'test.txt'
        storage_dir = 'storage'

        # Simulate a successful upload
        upload(file_path, storage_dir)

        # Verify the file existence check and directory creation
        mock_isfile.assert_called_once_with(file_path)
        mock_makedirs.assert_called_once_with(storage_dir, exist_ok=True)

        # Verify file copy and encryption
        mock_copy.assert_called_once_with(file_path, os.path.join(storage_dir, 'test.txt'))
        mock_encrypt.assert_called_once_with(os.path.join(storage_dir, 'test.txt'))
        mock_logger.assert_called_once_with('File uploaded: test.txt')

    @patch('file_operations.os.path.isfile', return_value=False)
    @patch('file_operations.logger.error')
    def test_upload_file_not_found(self, mock_logger, mock_isfile):
        file_path = 'nonexistent.txt'
        storage_dir = 'storage'

        # Simulate file not found
        with self.assertRaises(FileNotFoundError):
            upload(file_path, storage_dir)

        # Verify error logging
        mock_isfile.assert_called_once_with(file_path)
        mock_logger.assert_called_once_with('Upload failed: File does not exist.')

    @patch('file_operations.decrypt_file')
    @patch('file_operations.encrypt_file')
    @patch('file_operations.os.path.exists', side_effect=lambda x: x == os.path.join('storage', 'test.txt'))
    @patch('file_operations.os.makedirs')
    @patch('file_operations.shutil.copy')
    @patch('file_operations.logger.info')
    def test_download_success(self, mock_logger, mock_copy, mock_makedirs, mock_exists, mock_encrypt, mock_decrypt):
        file_name = 'test.txt'
        storage_dir = 'storage'
        download_dir = 'downloads'

        # Simulate a successful download
        download(file_name, download_dir, storage_dir)

        # Verify decrypt and re-encrypt process
        mock_decrypt.assert_called_once_with(os.path.join(storage_dir, file_name))
        mock_encrypt.assert_called_once_with(os.path.join(storage_dir, file_name))

        # Ensure `os.makedirs` is called since `mock_exists` should return `False` for the download directory
        mock_makedirs.assert_any_call(download_dir, exist_ok=True)

        # Verify file copy
        mock_copy.assert_called_once_with(os.path.join(storage_dir, file_name), os.path.join(download_dir, file_name))
        mock_logger.assert_called_once_with(f'File downloaded: {file_name} to {download_dir}')

    @patch('file_operations.os.path.exists', return_value=False)
    @patch('file_operations.logger.error')
    def test_download_file_not_found(self, mock_logger, mock_exists):
        file_name = 'nonexistent.txt'
        storage_dir = 'storage'
        download_dir = 'downloads'

        # Simulate file not found
        with self.assertRaises(FileNotFoundError):
            download(file_name, download_dir, storage_dir)

        # Verify error logging
        mock_logger.assert_called_once_with('Download failed: File does not exist.')

    @patch('file_operations.os.listdir', return_value=['file1.txt', 'file2.txt'])
    @patch('file_operations.os.path.isfile', side_effect=lambda x: True)
    @patch('file_operations.os.makedirs')
    @patch('file_operations.logger.info')
    def test_list_files(self, mock_logger, mock_makedirs, mock_isfile, mock_listdir):
        storage_dir = 'storage'

        # Simulate listing files
        files = list_files(storage_dir)

        # Verify the list of files
        self.assertEqual(files, ['file1.txt', 'file2.txt'])
        mock_logger.assert_called_once_with('Listed files.')
        mock_makedirs.assert_called_once_with(storage_dir, exist_ok=True)

    @patch('file_operations.os.path.exists', return_value=True)
    @patch('file_operations.os.remove')
    @patch('file_operations.logger.info')
    def test_delete_success(self, mock_logger, mock_remove, mock_exists):
        file_name = 'test.txt'
        storage_dir = 'storage'

        # Simulate successful deletion
        delete(file_name, storage_dir)

        # Verify file removal
        mock_exists.assert_called_once_with(os.path.join(storage_dir, file_name))
        mock_remove.assert_called_once_with(os.path.join(storage_dir, file_name))
        mock_logger.assert_called_once_with(f'File deleted: {file_name}')

    @patch('file_operations.os.path.exists', return_value=False)
    @patch('file_operations.logger.error')
    def test_delete_file_not_found(self, mock_logger, mock_exists):
        file_name = 'nonexistent.txt'
        storage_dir = 'storage'

        # Simulate file not found
        with self.assertRaises(FileNotFoundError):
            delete(file_name, storage_dir)

        # Verify error logging
        mock_logger.assert_called_once_with('Delete failed: File does not exist.')

    def test_sanitize_path_valid(self):
        sanitized = sanitize_path('file.txt', 'storage')
        self.assertEqual(sanitized, os.path.join('storage', 'file.txt'))

    def test_sanitize_path_invalid(self):
        with self.assertRaises(ValueError):
            sanitize_path('../file.txt', 'storage')
        with self.assertRaises(ValueError):
            sanitize_path('/absolute/path.txt', 'storage')

if __name__ == '__main__':
    unittest.main()
