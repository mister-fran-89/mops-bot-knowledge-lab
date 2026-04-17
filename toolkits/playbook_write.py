"""PlaybookWriteTools — Create and write playbook artifacts. (Stub — implementation in Task 5)"""

from agno.tools import Toolkit


class PlaybookWriteTools(Toolkit):
    def __init__(self, engine_dir: str, playbooks_dir: str):
        self.engine_dir = engine_dir
        self.playbooks_dir = playbooks_dir
        super().__init__(name="playbook_write", tools=[])
