from abc import ABC, abstractmethod
from typing import Dict

class RemoteCopyInterface(ABC):
    @abstractmethod
    def remote_copy_files(self, source_to_target_paths_map: Dict[str, str], destination):
        pass
