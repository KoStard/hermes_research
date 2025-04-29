import logging
import re
from typing import Optional

from ..config import HermesConfig
from . import HermesResearchMenuInterface, MenuSelection
from .menu_manager import MenuManager

logger = logging.getLogger(__name__)


class HermesResearchMenu(HermesResearchMenuInterface):
    """Provides an interactive menu for configuring a Hermes research task."""

    def __init__(self):
        self._config: Optional[HermesConfig] = None

    def set_config(self, config: HermesConfig):
        """Sets the configuration object needed for menu options."""
        self._config = config
        logger.debug("Configuration set for HermesResearchMenu.")

    def _validate_session_name(self, name: str) -> bool:
        """Checks if the session name is valid."""
        if not name:
            print("Error: Session name cannot be empty.")
            return False
        if not all(c.isalnum() or c in ('-', '_') for c in name) or ' ' in name:
            print(f"Error: Session name '{name}' should only contain letters, numbers, dashes, or underscores.")
            return False
        logger.debug(f"Session name '{name}' validated successfully.")
        return True

    def _prompt_for_session_name(self) -> str:
        """Prompts the user for a valid session name."""
        while True:
            try:
                session_name = MenuManager.text_prompt("Enter a name for this research session: ")
                if self._validate_session_name(session_name):
                    return session_name
            except KeyboardInterrupt:
                logger.info("Session name input cancelled by user.")
                raise  # Re-raise to allow cancellation propagation

    def _select_model(self) -> str:
        """Prompts the user to select a model from the config."""
        if not self._config or not self._config.models:
            logger.error("No models found in configuration.")
            raise ValueError("Configuration error: No models available for selection.")

        models = self._config.models
        logger.debug(f"Presenting models for selection: {models}")

        index = MenuManager.selection_menu("Select Model", models, allow_cancel=True)

        if index == -1:
            logger.info("Model selection cancelled by user.")
            raise KeyboardInterrupt("Model selection cancelled.")

        selected_model = models[index]
        logger.info(f"Model selected: {selected_model}")
        return selected_model

    def _prompt_for_budget(self) -> int:
        """Prompts the user for the budget, using the default from config."""
        if not self._config:
            logger.error("Configuration not set, cannot determine default budget.")
            raise ValueError("Configuration error: Cannot determine default budget.")

        default_budget = self._config.default_budget
        logger.debug(f"Default budget from config: {default_budget}")

        while True:
            try:
                budget_str = MenuManager.text_prompt(f"Enter budget (default: {default_budget}): ")
                if not budget_str:
                    logger.info(f"Using default budget: {default_budget}")
                    return default_budget
                try:
                    budget = int(budget_str)
                    if budget > 0:
                        logger.info(f"Budget set by user: {budget}")
                        return budget
                    else:
                        print("Error: Budget must be a positive integer.")
                except ValueError:
                    print("Error: Invalid input. Please enter a positive integer.")
            except KeyboardInterrupt:
                logger.info("Budget input cancelled by user.")
                raise  # Re-raise

    def _prompt_for_prompt(self) -> str:
        """Prompts the user for the multiline research prompt."""
        print("Enter the research prompt (press Meta+Enter or Esc+Enter to finish):")
        try:
            prompt_text = MenuManager.text_prompt("> ", multiline=True)
            if not prompt_text.strip():
                logger.warning("User entered an empty prompt.")
                # Allow empty prompts for now, maybe add confirmation later if needed
            logger.info("Prompt received from user.")
            return prompt_text
        except KeyboardInterrupt:
            logger.info("Prompt input cancelled by user.")
            raise  # Re-raise

    def _select_execution_target(self) -> Optional[str]:
        """Prompts the user to select local execution or a remote server."""
        if not self._config:
             logger.error("Configuration not set, cannot determine remote servers.")
             raise ValueError("Configuration error: Cannot determine remote servers.")

        options = ["Local Execution"]
        remote_server_names = list(self._config.remote_servers.keys())
        options.extend(remote_server_names)
        logger.debug(f"Presenting execution targets: {options}")

        index = MenuManager.selection_menu("Select Execution Target", options, allow_cancel=True)

        if index == -1:
            logger.info("Execution target selection cancelled by user.")
            raise KeyboardInterrupt("Execution target selection cancelled.")

        if index == 0:
            logger.info("Local execution selected.")
            return None  # None represents local execution
        else:
            selected_server_name = remote_server_names[index - 1]
            logger.info(f"Remote server selected: {selected_server_name}")
            return selected_server_name

    def get_selection(self) -> MenuSelection:
        """Runs the interactive menu and returns the user's selections."""
        if not self._config:
            logger.error("Configuration must be set before calling get_selection.")
            raise ValueError("Configuration not set. Call set_config first.")

        logger.info("Starting interactive menu for research task configuration.")
        try:
            session_name = self._prompt_for_session_name()
            model = self._select_model()
            budget = self._prompt_for_budget()
            prompt_text = self._prompt_for_prompt()
            selected_server_name = self._select_execution_target()

            selection = MenuSelection(
                session_name=session_name,
                model=model,
                budget=budget,
                prompt=prompt_text,
                selected_server_name=selected_server_name
            )
            return selection

        except KeyboardInterrupt:
            print("\nConfiguration cancelled.")
            logger.warning("Menu configuration cancelled by user (KeyboardInterrupt).")
            # Re-raise so the main application loop can handle it cleanly
            raise
        except Exception as e:
            logger.exception(f"An unexpected error occurred during menu interaction: {e}")
            print(f"\nAn error occurred: {e}")
            # Re-raise or handle more gracefully depending on desired app behavior
            raise
