# Simple boxed banner for AutoSeccomp-Gen (no extra deps; uses Rich only)
import os
import shutil
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text

def _get_version() -> str:
    """Return installed package version if available; otherwise empty string."""
    try:
        from importlib.metadata import version, PackageNotFoundError
        try:
            return version("autoseccomp-gen")
        except PackageNotFoundError:
            # Editable install or not installed as a dist: best-effort empty
            return ""
    except Exception:
        return ""

def print_banner() -> None:
    """Pretty boxed banner at CLI start. Disable with AUTOSECCOMP_NO_BANNER=1."""
    if os.getenv("AUTOSECCOMP_NO_BANNER") in {"1", "true", "yes", "on"}:
        return

    author = os.getenv("AUTOSECCOMP_AUTHOR", "Sebasteuo")
    ver = _get_version()

    title = Text("AUTOSECCOMP-GEN", style="bold cyan")
    subtitle = Text("trace → profile → validate", style="dim")

    # Center content based on current terminal width
    cols = shutil.get_terminal_size((80, 24)).columns
    body = Align.center(Text.assemble(title, "\n", subtitle), vertical="middle", width=min(cols-8, 100))

    footer = f"by {author}" + (f" • v{ver}" if ver else "")
    panel = Panel.fit(
        body,
        border_style="cyan",
        padding=(1, 4),
        subtitle=footer,
        subtitle_align="right",
    )
    Console().print(panel)
