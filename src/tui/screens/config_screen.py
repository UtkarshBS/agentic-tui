"""Provider configuration screen."""
from textual.screen import Screen
from textual.containers import Vertical
from textual.widgets import Input, Button, Label, Select, Static
import os


class ConfigScreen(Screen):
    DEFAULT_CSS = """
    ConfigScreen {
        layout: vertical;
        padding: 2;
    }
    """

    BINDINGS = [("escape", "pop_screen", "Back")]

    def __init__(self):
        self._providers = {
            "kimi": "KIMI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "nomic": "NOMIC_API_KEY",
            "lmstudio": "LMSTUDIO_API_KEY",
        }
        super().__init__()

    def compose(self) -> None:
        yield Label("Provider Configuration", classes="title")
        yield Static("Set API keys and select default model.")
        
        yield Label("Active Provider:")
        yield Select(
            [(p, p) for p in ["kimi", "anthropic", "openai", "ollama", "lmstudio", "mock"]],
            value=os.getenv("DEFAULT_PROVIDER", "lmstudio"),
            id="default-provider",
        )
        
        yield Label("LM Studio Settings:")
        yield Input(placeholder="LM Studio Base URL", value=os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1"), id="lmstudio-url")
        yield Input(placeholder="LM Studio Model", value=os.getenv("LMSTUDIO_MODEL", "qwen/qwen3.5-9b"), id="lmstudio-model")
        
        for name, env_var in self._providers.items():
            val = os.getenv(env_var, "")
            yield Input(placeholder=f"{name.upper()} API Key", value=val, password=True, id=f"key-{name}")
        
        yield Button("Save", variant="success", id="save")
        yield Button("Back", variant="primary", id="back")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "save":
            provider = self.query_one("#default-provider", Select).value
            os.environ["DEFAULT_PROVIDER"] = str(provider)
            
            lm_url = self.query_one("#lmstudio-url", Input).value.strip()
            lm_model = self.query_one("#lmstudio-model", Input).value.strip()
            if lm_url:
                os.environ["LMSTUDIO_BASE_URL"] = lm_url
            if lm_model:
                os.environ["LMSTUDIO_MODEL"] = lm_model
            
            for name, env_var in self._providers.items():
                key_input = self.query_one(f"#key-{name}", Input)
                val = key_input.value.strip()
                if val:
                    os.environ[env_var] = val
            
            self.notify(f"Saved! Provider: {provider}")
        self.app.pop_screen()

    def action_pop_screen(self):
        self.app.pop_screen()