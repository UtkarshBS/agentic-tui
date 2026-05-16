"""Code editing tools."""
from core.project import Project
from tools.base import ToolRegistry


def register_edit_tools(registry: ToolRegistry, project: Project):
    @registry.register(description="Exact string replacement in a file. old_string must match exactly.")
    def find_replace(path: str, old_string: str, new_string: str) -> str:
        try:
            content = project.read_file(path)
            if old_string not in content:
                return f"Error: old_string not found in {path}"
            new_content = content.replace(old_string, new_string, 1)
            project.write_file(path, new_content)
            return f"Updated {path}"
        except Exception as e:
            return f"Error: {e}"

    @registry.register(description="Apply a unified diff patch.")
    def apply_patch(path: str, patch: str) -> str:
        return "Patch tool not yet implemented; use find_replace."
