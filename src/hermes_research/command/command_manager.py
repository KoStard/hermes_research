import os
import re
from typing import List
from hermes_research.command import HermesResearchCommandManagerInterface


class HermesResearchCommandManager(HermesResearchCommandManagerInterface):
    def generate_command(self, path_to_research: str, model: str, files: List[str], budget: int, prompt: str, extra_arguments: str = "") -> str:
        """
        Generate a formatted Hermes CLI command with the given parameters.
        Args:
            path_to_research: Path to the deep research directory
            model: The model identifier to use
            files: List of file paths to include as textual files
            budget: Deep research budget value
            prompt: The query prompt text
        
        Returns:
            A formatted command string with proper escaping and line breaks
        """
        # Escape special characters in prompt
        escaped_prompt = prompt.replace('"', '\\"').replace('$', '\\$')
        
        # Start building the command
        command_parts = [
            'hermes chat',
            f'--model {model}',
            f'--deep-research {path_to_research}',
            f'--set_deep_research_budget {budget}',
            f'--text "{escaped_prompt}"',
        ]

        # Add files if provided
        for file_path in files:
            command_parts.append(f'--textual_file "{file_path}"')

        # Add extra arguments if provided
        if extra_arguments:
            command_parts.append(extra_arguments)

        # Join with line continuation for readability
        return " \\\n    ".join(command_parts)

    def save_command_in_file(self, command, path):
        pass