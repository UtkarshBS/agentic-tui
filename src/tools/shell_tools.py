"""Shell and git tools."""
import subprocess
from core.project import Project
from tools.base import ToolRegistry


def register_shell_tools(registry: ToolRegistry, project: Project):
    @registry.register(description="Run a shell command. Timeout 30s.")
    def run_command(command: str, cwd: str = None) -> str:
        try:
            work = project.root if cwd is None else (project.root / cwd)
            r = subprocess.run(command, shell=True, cwd=str(work), capture_output=True, text=True, timeout=30)
            out = f"Exit {r.returncode}\n{r.stdout}"
            if r.stderr:
                out += f"\nSTDERR:\n{r.stderr}"
            return out
        except Exception as e:
            return f"Error: {e}"

    @registry.register(description="Git status.")
    def git_status() -> str:
        return project.git_status()

    @registry.register(description="Git diff.")
    def git_diff() -> str:
        return project.git_diff()
