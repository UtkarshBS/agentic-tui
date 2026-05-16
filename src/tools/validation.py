"""Post-edit validation."""
import ast
from pathlib import Path
from core.project import Project


class Validator:
    def __init__(self, project: Project):
        self.project = project

    def validate_python(self, path: str) -> str:
        try:
            ast.parse(self.project.read_file(path))
            return "OK"
        except SyntaxError as e:
            return f"SyntaxError: {e}"

    def validate(self, path: str) -> str:
        ext = Path(path).suffix
        if ext == ".py":
            return self.validate_python(path)
        return "No validator for this file type"
