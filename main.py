import argparse
from auth import authenticate, is_authenticated, get_current_user
from file_operations import upload, download, list_files, delete
from logger import logger
import os
from config import Config
import sys
from datetime import datetime


def init_app():
    """
    Initializes the cli application,sets
    local for storage,token,log_file and encryption key.
    """
    os.makedirs(Config.STORAGE_DIR, exist_ok=True)
    os.makedirs(Config.TOKENS_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(Config.LOG_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(Config.AES_KEY_FILE), exist_ok=True)
    logger.info("Application initialized.")
    print("Application initialized.")


def main():
    """Cli entry point"""
    parser = argparse.ArgumentParser(
        description="Secure File Storage System (SFSS)",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    subparsers = parser.add_subparsers(
        dest="command", help="Available commands", required=True
    )

    # Init command
    init = subparsers.add_parser("init", help="Initialize the application")

    # Auth command
    auth = subparsers.add_parser("auth", help="Authenticate user with GitHub portal")

    # Upload command
    upload_parser = subparsers.add_parser(
        "upload", help="Upload a file to local storage system"
    )
    upload_parser.add_argument("file_path", type=str, help="Path of file to upload")

    # Download command
    download_parser = subparsers.add_parser("download", help="Download a file")
    download_parser.add_argument(
        "file_name", type=str, help="Name of the file to download"
    )
    download_parser.add_argument(
        "download_dir", type=str, help="Directory to download the file to"
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List all files")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a file")
    delete_parser.add_argument("file_name", type=str, help="Name of the file to delete")

    args = parser.parse_args()

    # List of operations that cli can manage.
    if args.command == "init":
        init_app()
        sys.exit(0)

    elif args.command == "auth":
        token = authenticate()
        if token:
            print("Authentication successful.")
        else:
            print("Authentication failed.")
        sys.exit(0)  # Exit after authentication

    elif args.command:
        if not is_authenticated():
            print('You must authenticate first using the "auth" command.')
            logger.warning("Unauthorized access attempt.")
            sys.exit(1)

        current_user = get_current_user()
        if not current_user:
            print("Unable to retrieve current user information.")
            logger.error("Failed to retrieve current user.")
            sys.exit(1)

        username = current_user["username"]
        user_storage_dir = os.path.join(Config.STORAGE_DIR, username)
        os.makedirs(user_storage_dir, exist_ok=True)

        if args.command == "upload":
            try:
                upload(args.file_path, user_storage_dir)
                print("File uploaded successfully.")
                logger.info(f"File uploaded: {args.file_path} by user {username}")
            except Exception as e:
                logger.error(f"Upload error: {e}")
                print("Upload failed.")

        elif args.command == "download":
            try:
                download(args.file_name, args.download_dir, user_storage_dir)
                print("File downloaded successfully.")
                logger.info(
                    f"File downloaded: {args.file_name} to {args.download_dir} by user {username}"
                )
            except Exception as e:
                logger.error(f"Download error: {e}")
                print("Download failed.")

        elif args.command == "list":
            try:
                files = list_files(user_storage_dir)
                print("Stored Files:")
                for f in files:
                    print(f)
                logger.info(f"Listed files for user {username}.")
            except Exception as e:
                logger.error(f"List error: {e}")
                print("Failed to list files.")

        elif args.command == "delete":
            try:
                delete(args.file_name, user_storage_dir)
                print("File deleted successfully.")
                logger.info(f"File deleted: {args.file_name} by user {username}")
            except Exception as e:
                logger.error(f"Delete error: {e}")
                print("Delete failed.")


if __name__ == "__main__":
    main()
