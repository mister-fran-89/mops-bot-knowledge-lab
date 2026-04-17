"""SQLExecutionTools — Execute SQL against Redshift. (Stub — implementation in Task 4)"""

from agno.tools import Toolkit


class SQLExecutionTools(Toolkit):
    def __init__(self, playbooks_dir: str, results_dir: str = "./data/results"):
        self.playbooks_dir = playbooks_dir
        self.results_dir = results_dir
        super().__init__(name="sql_execution", tools=[])
