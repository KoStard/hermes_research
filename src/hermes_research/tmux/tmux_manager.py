import logging
import os
import shlex
import subprocess
from typing import List, Optional

from . import TmuxManagerInterface
from .ssh import SSHConnectionInterface, SSHDestination

logger = logging.getLogger(__name__)


class _UnsetTmuxEnv:
    """Context manager for temporarily unsetting the TMUX environment variable."""

    def __enter__(self):
        self.original_value = os.environ.get("TMUX")
        if "TMUX" in os.environ:
            logger.debug("Temporarily unsetting TMUX environment variable.")
            del os.environ["TMUX"]
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.original_value is not None:
            logger.debug("Restoring TMUX environment variable.")
            os.environ["TMUX"] = self.original_value
        elif "TMUX" in os.environ:
            # If it was set during the context, ensure it's removed if it wasn't there originally
            del os.environ["TMUX"]
