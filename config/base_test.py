import os


class BaseTest:
    def setup_method(self):
        self.project_root = os.path.dirname(os.path.dirname(__file__))
        self.fixtures_path = os.path.join(self.project_root, "fixtures")
        self.test_file_path = os.path.join(self.fixtures_path, "for_testing", "test_task_positive.pdf")
        self.master_file_path = os.path.join(self.fixtures_path, "master.pdf")
        self.master_data_file_path = os.path.join(self.fixtures_path, "master_data.json")
