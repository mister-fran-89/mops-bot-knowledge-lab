"""SQLComparisonTools — Structural SQL comparison. (Stub — implementation in Task 3)"""

from agno.tools import Toolkit


class SQLComparisonTools(Toolkit):
    def __init__(self, playbooks_dir: str):
        self.playbooks_dir = playbooks_dir
        super().__init__(name="sql_comparison", tools=[])
