from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseAdapter(ABC):
    """
    Abstract Base Class for all platform adapters.
    Ensures a consistent interface for the Dispatcher to interact with different platforms.
    """

    @abstractmethod
    def verify_auth(self, account_id: str) -> bool:
        """
        Verify if the account credentials are still valid.
        Args:
            account_id: The unique identifier for the account in the Auth store.
        Returns:
            bool: True if authenticated, False otherwise.
        """
        pass

    @abstractmethod
    def upload_media(self, file_path: str) -> str:
        """
        Upload a media file (image/video) to the platform's servers.
        Args:
            file_path: Absolute path to the media file.
        Returns:
            str: The URL or Media ID returned by the platform.
        """
        pass

    @abstractmethod
    def post(self, content: Dict[str, Any]) -> str:
        """
        Execute the final post operation using the resolved content.
        Args:
            content: A dictionary containing resolved variables (title, body, etc.).
        Returns:
            str: The URL of the created post or a success message.
        """
        pass
