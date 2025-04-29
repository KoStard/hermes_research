import logging
from typing import Optional

from hermes_research.tmux import TmuxManagerInterface
from hermes_research.preparation.menu.menu_manager import MenuManager
from . import SessionNameManagerInterface

logger = logging.getLogger(__name__)

class SessionNameManager(SessionNameManagerInterface):
    """Manages tmux session name conflicts."""
    
    def __init__(self, tmux_manager: TmuxManagerInterface):
        """Initialize with a TmuxManager to check for existing sessions.
        
        Args:
            tmux_manager: TmuxManagerInterface implementation for session operations
        """
        self.tmux_manager = tmux_manager
    
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
        original_session_name = session_name
        context = f"on server '{server_name}'" if is_remote else "locally"
        
        while self.tmux_manager.session_exists(session_name):
            logger.warning(f"Tmux session '{session_name}' already exists {context}.")
            
            action = MenuManager.selection_menu(
                f"Tmux session '{session_name}' already exists {context}.",
                ["Kill existing session and proceed", "Enter a new session name", "Cancel"],
                allow_cancel=False  # Force a choice
            )
            
            if action == 0:  # Kill and proceed
                logger.info(f"User chose to kill existing session '{session_name}' {context}.")
                try:
                    self.tmux_manager.kill_session(session_name)
                    break  # Exit loop, proceed with original name
                except Exception as e:
                    logger.error(f"Failed to kill session '{session_name}' {context}: {e}")
                    logger.error(f"Could not kill existing session '{session_name}' {context}.")
                    continue
            elif action == 1:  # Enter new name
                try:
                    new_name = MenuManager.text_prompt("Enter new session name: ")
                    # Basic validation
                    if new_name and not self.tmux_manager.session_exists(new_name):
                        session_name = new_name
                        logger.info(f"Using new session name: '{session_name}' {context}")
                        
                        # The original research path was already determined
                        if is_remote:
                            logger.warning(f"Remote research files will still be in '{original_session_name}' directory.")
                        else:
                            logger.warning(f"Research files will still be in '{original_session_name}' directory.")
                        
                        break  # Exit loop, proceed with new name
                    elif not new_name:
                        logger.error("Session name cannot be empty.")
                    else:
                        logger.error(f"Session '{new_name}' also exists {context}.")
                except KeyboardInterrupt:
                    raise  # Propagate cancellation
            else:  # Cancel
                logger.warning(f"User cancelled due to existing tmux session {context}.")
                logger.info("Operation cancelled.")
                raise KeyboardInterrupt()  # Raise to signal cancellation
        
        return session_name
