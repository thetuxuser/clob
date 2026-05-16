"""clob — Universal AI in your terminal.

Entry point for CLI and TUI.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from pathlib import Path
import sys
from typing import Annotated, Optional

import typer

app = typer.Typer(
    name="clob",
    help="Universal AI in your terminal.",
    rich_markup_mode="rich",
    no_args_is_help=False,
)


def _get_config():
    from .config.settings import AppConfig
    return AppConfig.load()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[bool, typer.Option("--version", "-v", help="Show version")] = False,
) -> None:
    """[bold blue]clob[/bold blue] — Universal AI in your terminal."""
    if version:
        from . import __version__
        typer.echo(f"clob {__version__}")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        # Launch TUI
        _launch_tui()


def _launch_tui() -> None:
    """Launch the Textual TUI."""
    try:
        from .tui.app import ClobApp
        config = _get_config()
        app_instance = ClobApp(config)
        app_instance.run()
    except ImportError as e:
        typer.echo(f"[red]Failed to launch TUI: {e}[/red]")
        typer.echo("Install TUI dependencies: pip install clob[tui]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        pass


@app.command("chat")
def chat_cmd(
    message: Annotated[str, typer.Argument(help="Message to send")] = "",
    provider: Annotated[Optional[str], typer.Option("--provider", "-p")] = None,
    model: Annotated[Optional[str], typer.Option("--model", "-m")] = None,
    no_stream: Annotated[bool, typer.Option("--no-stream")] = False,
) -> None:
    """Send a single chat message (non-TUI mode)."""
    if not message:
        typer.echo("Usage: clob chat 'your message'")
        raise typer.Exit(1)

    async def _run():
        from .core.runtime import Runtime
        config = _get_config()
        runtime = Runtime(config)
        if provider:
            runtime.set_provider(provider)
        if model:
            runtime.set_model(model)
        await runtime.start()
        try:
            if no_stream:
                response = await runtime.chat(message)
                typer.echo(response)
            else:
                async for chunk in runtime.stream_response(message):
                    if chunk.delta:
                        typer.echo(chunk.delta, nl=False)
                typer.echo()
        finally:
            await runtime.stop()

    asyncio.run(_run())


@app.command("models")
def models_cmd(
    provider: Annotated[Optional[str], typer.Option("--provider", "-p")] = None,
) -> None:
    """List available models."""
    async def _run():
        from .providers.registry import ProviderRegistry
        config = _get_config()
        reg = ProviderRegistry()
        reg.load_from_config(config)

        providers_to_check = [provider] if provider else reg.list_names()
        for pname in providers_to_check:
            prov = reg.get(pname)
            if not prov:
                continue
            typer.echo(f"\n[{pname}]")
            try:
                models = await prov.list_models()
                for m in models[:20]:
                    typer.echo(f"  {m.id}")
                if len(models) > 20:
                    typer.echo(f"  ... and {len(models) - 20} more")
            except Exception as e:
                typer.echo(f"  Error: {e}")
        await reg.close_all()

    asyncio.run(_run())


@app.command("providers")
def providers_cmd() -> None:
    """List configured providers."""
    config = _get_config()
    typer.echo("\nConfigured providers:")
    for name, pconf in config.providers.items():
        key_status = "✓" if pconf.api_key else "✗ (no key)"
        typer.echo(f"  {name:15} {pconf.base_url:40} {key_status}")


@app.command("config")
def config_cmd(
    edit: Annotated[bool, typer.Option("--edit", "-e", help="Open config in editor")] = False,
    show: Annotated[bool, typer.Option("--show", "-s", help="Show config path")] = False,
) -> None:
    """Manage clob configuration."""
    from .config.settings import CONFIG_FILE
    if show or not edit:
        typer.echo(f"Config file: {CONFIG_FILE}")
        if CONFIG_FILE.exists():
            typer.echo(CONFIG_FILE.read_text())
    if edit:
        import os, subprocess
        editor = os.environ.get("EDITOR", "nano")
        subprocess.run([editor, str(CONFIG_FILE)])


@app.command("memory")
def memory_cmd(
    search: Annotated[Optional[str], typer.Option("--search", "-s")] = None,
    sessions: Annotated[bool, typer.Option("--sessions")] = False,
) -> None:
    """Search memory / list sessions."""
    async def _run():
        from .memory.manager import MemoryManager
        mm = MemoryManager()
        await mm.start()
        try:
            if search:
                results = await mm.search(search)
                for msg in results:
                    typer.echo(f"[{msg.role}] {msg.content[:100]}")
            else:
                sessions_list = await mm.get_sessions()
                for s in sessions_list:
                    typer.echo(f"  #{s.id:3}  {s.title[:50]:50}  {s.provider}/{s.model}")
        finally:
            await mm.stop()

    asyncio.run(_run())


@app.command("doctor")
def doctor_cmd() -> None:
    """Check clob installation and provider connectivity."""
    from .config.settings import CONFIG_FILE, DB_FILE

    typer.echo("🩺 clob doctor\n")

    # Config
    typer.echo(f"Config: {'✓' if CONFIG_FILE.exists() else '✗ (not found)'}  {CONFIG_FILE}")
    typer.echo(f"DB:     {'✓' if DB_FILE.exists() else '○ (will be created)'}  {DB_FILE}")

    # Python version
    import sys
    typer.echo(f"Python: {sys.version.split()[0]}")

    # Dependencies
    deps = ["textual", "httpx", "pydantic", "aiosqlite", "typer", "rich"]
    for dep in deps:
        try:
            __import__(dep)
            typer.echo(f"  ✓ {dep}")
        except ImportError:
            typer.echo(f"  ✗ {dep} (missing)")

    # Provider connectivity
    async def _check():
        from .providers.registry import ProviderRegistry
        config = _get_config()
        reg = ProviderRegistry()
        reg.load_from_config(config)
        typer.echo("\nProvider connectivity:")
        for name in reg.list_names():
            prov = reg.get(name)
            ok = await prov.health_check()
            typer.echo(f"  {'✓' if ok else '✗'} {name}")
        await reg.close_all()

    asyncio.run(_check())


@app.command("ollama")
def ollama_cmd(
    action: Annotated[str, typer.Argument(help="Action: list | pull | chat")] = "list",
    model: Annotated[Optional[str], typer.Argument()] = None,
) -> None:
    """Manage Ollama local models."""
    async def _run():
        from .providers.ollama import OllamaProvider
        from .config.settings import ProviderConfig
        config = _get_config()
        pconf = config.get_provider("ollama") or ProviderConfig(name="ollama", base_url="http://localhost:11434")
        ollama = OllamaProvider(pconf)

        if action == "list":
            models = await ollama.list_models()
            if models:
                typer.echo("Local Ollama models:")
                for m in models:
                    typer.echo(f"  {m.id}")
            else:
                typer.echo("No models found (is Ollama running?)")
        elif action == "pull" and model:
            typer.echo(f"Pulling {model}...")
            async for status in ollama.pull_model(model):
                typer.echo(f"\r{status}", nl=False)
            typer.echo("\nDone!")
        else:
            typer.echo("Usage: clob ollama list | clob ollama pull <model>")

        await ollama.close()

    asyncio.run(_run())


if __name__ == "__main__":
    app()


# ── v0.2.0 commands ───────────────────────────────────────────────────────────

@app.command("workspace")
def workspace_cmd(
    action: Annotated[str, typer.Argument(help="Action: index | stats | context")] = "stats",
    path: Annotated[Optional[str], typer.Argument()] = None,
) -> None:
    """Workspace indexing and context tools."""
    from .indexing import index_workspace

    target = Path(path) if path else Path.cwd()

    if action == "index":
        typer.echo(f"Indexing {target}…")
        idx = index_workspace(target)
        typer.echo(idx.stats_report())
    elif action == "stats":
        idx = index_workspace(target)
        typer.echo(idx.stats_report())
    elif action == "context":
        from .workspace import workspace_summary
        typer.echo(workspace_summary(target))
    else:
        typer.echo(f"Unknown action: {action}. Use: index | stats | context")


@app.command("session")
def session_cmd(
    export: Annotated[Optional[int], typer.Option("--export", "-e", help="Export session ID")] = None,
    delete: Annotated[Optional[int], typer.Option("--delete", "-d", help="Delete session ID")] = None,
    fmt: Annotated[str, typer.Option("--format", "-f", help="Export format: md | json")] = "md",
) -> None:
    """Manage sessions: export or delete."""
    async def _run():
        from .memory.manager import MemoryManager
        mm = MemoryManager()
        await mm.start()
        try:
            if export is not None:
                msgs = await mm.get_history(export)
                if not msgs:
                    typer.echo(f"Session {export} not found or empty.")
                    return
                if fmt == "json":
                    data = [{"role": m.role, "content": m.content, "ts": str(m.created_at)} for m in msgs]
                    out = f"session-{export}.json"
                    Path(out).write_text(json.dumps(data, indent=2))
                else:
                    lines = [f"# Session {export} Export\n"]
                    for m in msgs:
                        lines.append(f"**{m.role.title()}:** {m.content}\n")
                    out = f"session-{export}.md"
                    Path(out).write_text("\n".join(lines))
                typer.echo(f"Exported to {out}")
            elif delete is not None:
                await mm.delete_session(delete)
                typer.echo(f"Session {delete} deleted.")
            else:
                sessions = await mm.get_sessions()
                for s in sessions:
                    typer.echo(f"  #{s.id:3}  {s.title[:50]:50}  {s.provider}")
        finally:
            await mm.stop()

    import json
    asyncio.run(_run())


@app.command("plugins")
def plugins_cmd(
    action: Annotated[str, typer.Argument(help="Action: list | install")] = "list",
    name: Annotated[Optional[str], typer.Argument()] = None,
) -> None:
    """Manage clob plugins."""
    if action == "list":
        from .plugins.loader import plugin_loader, PLUGINS_DIR
        loaded = plugin_loader.load_all()
        if loaded:
            typer.echo("Installed plugins:")
            for p in loaded:
                plugin = plugin_loader.get(p)
                typer.echo(f"  {p:20} v{getattr(plugin, 'version', '?'):8}  {getattr(plugin, 'description', '')}")
        else:
            typer.echo(f"No plugins found in {PLUGINS_DIR}")
            typer.echo("Create plugins in ~/.config/clob/plugins/<name>/plugin.py")
    elif action == "install" and name:
        typer.echo(f"Installing {name} via pip…")
        import subprocess
        subprocess.run(["pip", "install", name])
        typer.echo("Done! Restart clob to activate the plugin.")
    else:
        typer.echo("Usage: clob plugins list | clob plugins install <package>")


@app.command("usage")
def usage_cmd() -> None:
    """Show token and cost usage for this session."""
    typer.echo("Usage tracking is available inside the TUI (Ctrl+U) or after running 'clob chat'.")
    typer.echo("Start a session with 'clob' to see live token analytics.")


@app.command("theme")
def theme_cmd(
    action: Annotated[str, typer.Argument(help="Action: list | set")] = "list",
    name: Annotated[Optional[str], typer.Argument()] = None,
) -> None:
    """Manage TUI themes."""
    from .themes import list_themes, get_theme
    if action == "list":
        themes = list_themes()
        typer.echo("Available themes:")
        for t in themes:
            theme = get_theme(t)
            typer.echo(f"  {t:15}  {theme.description}")
    elif action == "set" and name:
        theme = get_theme(name)
        config = _get_config()
        config.default.theme = name
        config.save()
        typer.echo(f"Theme set to '{name}'. Restart clob to apply.")
    else:
        typer.echo("Usage: clob theme list | clob theme set <name>")
