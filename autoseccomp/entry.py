import os
from pathlib import Path
from typing import Optional

# NOTE: Only standard library; comments in English by request.

def _load_author_from_config() -> Optional[str]:
    """Read author from config file(s), if present."""
    try:
        import tomllib  # Python 3.11+
    except Exception:
        return None

    candidates = [
        # Highest priority: XDG config
        Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "autoseccomp" / "config.toml",
        # Fallbacks
        Path.home() / ".config" / "autoseccomp" / "config.toml",
        Path("/etc/autoseccomp/config.toml"),
    ]
    for p in candidates:
        try:
            if p.exists():
                with p.open("rb") as fh:
                    data = tomllib.load(fh)
                ui = data.get("ui", {})
                author = ui.get("author")
                if isinstance(author, str) and author.strip():
                    return author.strip()
        except Exception:
            # Silently ignore malformed config; no hard failure for CLI
            pass
    return None


def _should_show_banner() -> bool:
    """Allow disabling via env var in CI, default ON."""
    val = os.environ.get("AUTOSECCOMP_BANNER", "1").strip().lower()
    return val not in {"0", "false", "no", "off"}


def _render_box(lines):
    """Simple ASCII box; width adapts to longest line."""
    width = max(len(s) for s in lines)
    top = "+" + "-" * (width + 2) + "+"
    bot = top
    body = [f"| {s.ljust(width)} |" for s in lines]
    return "\n".join([top, *body, bot])


def print_banner():
    """Print the banner unless disabled."""
    if not _should_show_banner():
        return
    author = os.environ.get("AUTOSECCOMP_AUTHOR") or _load_author_from_config()
    lines = ["AutoSeccomp-Gen  ·  Trace → Generate → Validate"]
    if author:
        lines.append(f"Author: {author}")
    lines.append("https://github.com/Sebasteuo/autoseccomp-gen")
    print(_render_box(lines))
    print()  # extra blank line


def main():
    """Wrapper entrypoint: print banner, then run CLI."""
    print_banner()
    # Defer import so CLI pays zero cost when banner is disabled
    from autoseccomp.cli import main as cli_main
    cli_main()
