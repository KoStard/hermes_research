from abc import ABC, abstractmethod
from typing import Optional

class SessionNameManagerInterface(ABC):
    @abstractmethod
    def handle_session_name_conflict(self, session_name: str, is_remote: bool = False, server_name: Optional[str] = None) -> str:
        """Handle conflicts when a tmux session with the same name already exists.
        
        Args:
            session_name: The desired session name
            is_remote: Whether this is for a remote session
            server_name: Name of the remote server (if is_remote=True)
            
        Returns:
            The final session name to use, may be the same as input
            
        Raises:
            KeyboardInterrupt: If user cancels the operation
        """
        pass
