import os
from metrics_scripts import helper as hp


class FanInOut:
    """
    Fan-Out per release e Fan-In total cumulativo.
    """

    def __init__(self):
        self.fan_in_map = {}

    def _normalize_class_name(self, class_path):
        return class_path.split(os.sep)[-1].replace(".java", "")

    def compute_fan_out(self, file_content):
        dependencies = hp.extract_project_dependencies(file_content)
        dependencies = {d.strip() for d in dependencies if d}
        return len(dependencies), dependencies

    def update_fan_in(self, class_id, dependencies):
        current_class = self._normalize_class_name(class_id)

        for dep in dependencies:
            dep_clean = dep.strip()
            if not dep_clean:
                continue

            if dep_clean not in self.fan_in_map:
                self.fan_in_map[dep_clean] = set()

            self.fan_in_map[dep_clean].add(current_class)

    def get_fan_in_total(self, class_id):
        class_name = self._normalize_class_name(class_id)
        return len(self.fan_in_map.get(class_name, set()))