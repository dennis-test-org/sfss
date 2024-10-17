import os
import shutil
from encryption import encrypt_file, decrypt_file
from logger import logger


def sanitize_path(file_name, storage_dir):
    # Prevent path traversal
    if ".." in file_name or file_name.startswith("/"):
        raise ValueError("Invalid file name.")
    return os.path.join(storage_dir, file_name)


def upload(file_path, storage_dir):
    if not os.path.isfile(file_path):
        logger.error("Upload failed: File does not exist.")
        raise FileNotFoundError("File does not exist.")
    os.makedirs(storage_dir, exist_ok=True)
    file_name = os.path.basename(file_path)
    dest_path = sanitize_path(file_name, storage_dir)
    shutil.copy(file_path, dest_path)
    encrypt_file(dest_path)
    logger.info(f"File uploaded: {file_name}")


def download(file_name, download_dir, storage_dir):
    dest_path = sanitize_path(file_name, storage_dir)
    if not os.path.exists(dest_path):
        logger.error("Download failed: File does not exist.")
        raise FileNotFoundError("File does not exist.")
    decrypt_file(dest_path)
    if not os.path.exists(download_dir):
        os.makedirs(download_dir, exist_ok=True)
    shutil.copy(dest_path, os.path.join(download_dir, file_name))
    encrypt_file(dest_path)
    logger.info(f"File downloaded: {file_name} to {download_dir}")


def list_files(storage_dir):
    os.makedirs(storage_dir, exist_ok=True)
    files = [
        f
        for f in os.listdir(storage_dir)
        if os.path.isfile(os.path.join(storage_dir, f))
    ]
    logger.info("Listed files.")
    return files


def delete(file_name, storage_dir):
    file_path = sanitize_path(file_name, storage_dir)
    if not os.path.exists(file_path):
        logger.error("Delete failed: File does not exist.")
        raise FileNotFoundError("File does not exist.")
    os.remove(file_path)
    logger.info(f"File deleted: {file_name}")
