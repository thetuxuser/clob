"""clob v0.3.0 full test suite."""

from __future__ import annotations

import pytest


# ── Config ──────────────────────────────────────────────────
def test_provider_config_resolves_env(monkeypatch):
    monkeypatch.setenv("TEST_KEY", "secret123")
    from clob.config.settings import ProviderConfig

    conf = ProviderConfig(name="test", base_url="https://example.com", api_key="env:TEST_KEY")
    assert conf.api_key == "secret123"


def test_app_config_defaults():
    from clob.config.settings import AppConfig

    config = AppConfig()
    assert config.default.provider == "openrouter"


def test_config_profiles():
    from clob.config.settings import AppConfig

    config = AppConfig()
    config.profiles = {"local": {"provider": "ollama", "model": "llama3"}}
    assert config.apply_profile("local") is True
    assert config.default.provider == "ollama"


def test_config_profiles_missing():
    from clob.config.settings import AppConfig

    assert AppConfig().apply_profile("nope") is False


# ── Providers ──────────────────────────────────────────────
def test_model_info():
    from clob.providers.base import ModelInfo

    m = ModelInfo(id="gpt-4o", provider="openrouter")
    assert m.id == "gpt-4o"


def test_registry_empty():
    from clob.providers.registry import ProviderRegistry

    reg = ProviderRegistry()
    assert reg.list_names() == []


# ── Capabilities ───────────────────────────────────────────
def test_capabilities_openrouter():
    from clob.providers.capabilities import get_capabilities

    caps = get_capabilities("openrouter")
    assert caps.chat and caps.streaming and caps.tool_calling


def test_capabilities_ollama():
    from clob.providers.capabilities import get_capabilities

    caps = get_capabilities("ollama")
    assert caps.embeddings and not caps.image_generation


def test_capabilities_badges():
    from clob.providers.capabilities import get_capabilities

    badges = get_capabilities("nvidia").badge_list()
    assert len(badges) > 0


# ── Memory ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_database(tmp_path):
    from clob.memory.persistence import Database

    db = Database(tmp_path / "test.db")
    await db.connect()
    session = await db.create_session("Test", "openrouter", "gpt-4o")
    assert session.id is not None
    msg = await db.add_message(session.id, "user", "Hello!")
    assert msg.content == "Hello!"
    msgs = await db.get_messages(session.id)
    assert len(msgs) == 1
    await db.close()


@pytest.mark.asyncio
async def test_memory_search(tmp_path):
    from clob.memory.manager import MemoryManager

    mm = MemoryManager(tmp_path / "mm.db")
    await mm.start()
    s = await mm.new_session("groq", "llama3")
    await mm.add_message(s.id, "user", "Python decorators explained")
    results = await mm.search("Python")
    assert len(results) >= 1
    assert len(await mm.search("zzz_not_found")) == 0
    await mm.stop()


# ── Tools ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_shell_blocks():
    from clob.tools.shell import run_shell

    r = await run_shell("rm -rf /tmp/xyz", safe_mode=True)
    assert r.returncode == 1


@pytest.mark.asyncio
async def test_shell_echo():
    from clob.tools.shell import run_shell

    r = await run_shell("echo hello clob", safe_mode=True)
    assert "hello clob" in r.stdout


# ── Analytics ──────────────────────────────────────────────
def test_analytics_tracker():
    from clob.analytics import AnalyticsTracker, TurnStats

    t = AnalyticsTracker()
    turn = TurnStats("groq", "llama3", 100, 200, 500.0)
    t.record(1, turn)
    s = t.get_session(1)
    assert s.total_tokens == 300 and s.turn_count == 1


def test_analytics_free_provider():
    from clob.analytics import TurnStats

    assert TurnStats("ollama", "llama3", 1000, 500, 100.0).estimated_cost_usd == 0.0


def test_analytics_paid_provider():
    from clob.analytics import TurnStats

    assert (
        TurnStats("openrouter", "openai/gpt-4o", 1_000_000, 500_000, 5000.0).estimated_cost_usd > 0
    )


def test_analytics_summary_line():
    from clob.analytics import AnalyticsTracker, TurnStats

    t = AnalyticsTracker()
    t.record(1, TurnStats("ollama", "llama3", 50, 100, 200.0))
    line = t.get_session(1).summary_line()
    assert "↑" in line and "↓" in line


# ── Workspace ──────────────────────────────────────────────
def test_workspace_summary(tmp_path):
    from clob.workspace import workspace_summary

    (tmp_path / "main.py").write_text("print('hello')")
    result = workspace_summary(tmp_path)
    assert "Workspace" in result


def test_read_file_context(tmp_path):
    from clob.workspace import read_file_context

    f = tmp_path / "test.py"
    f.write_text("def hello(): pass")
    result = read_file_context(f)
    assert "hello" in result and "```" in result


def test_resolve_no_refs():
    from clob.workspace import resolve_context_refs

    assert resolve_context_refs("just a message") == "just a message"


def test_read_dir_context(tmp_path):
    from clob.workspace import read_dir_context

    (tmp_path / "a.py").write_text("x = 1")
    assert "Directory" in read_dir_context(tmp_path)


# ── Indexer ────────────────────────────────────────────────
def test_workspace_index(tmp_path):
    from clob.indexing import index_workspace

    (tmp_path / "main.py").write_text("print('clob')")
    (tmp_path / "utils.py").write_text("def helper(): pass")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "x.pyc").write_bytes(b"\x00")
    idx = index_workspace(tmp_path)
    assert idx.total_files == 2


def test_workspace_index_search(tmp_path):
    from clob.indexing import index_workspace

    (tmp_path / "database.py").write_text("# db")
    (tmp_path / "api.py").write_text("# api")
    idx = index_workspace(tmp_path)
    assert any("database" in r.rel_path for r in idx.search("data"))


# ── Streaming widget ───────────────────────────────────────
def test_streaming_append():
    from clob.tui.widgets import StreamingMarkdownWidget

    w = StreamingMarkdownWidget()
    w.append_token("Hello ")
    w.append_token("world")
    assert w.full_text == "Hello world" and w.token_count == 2


def test_streaming_fence():
    from clob.tui.widgets import StreamingMarkdownWidget

    w = StreamingMarkdownWidget()
    w.append_token("```python\n")
    assert w._in_fence
    w.append_token("x=1\n")
    w.append_token("```")
    assert not w._in_fence


def test_streaming_finalize():
    from clob.tui.widgets import StreamingMarkdownWidget

    w = StreamingMarkdownWidget()
    w.append_token("done")
    w.finalize()
    assert w._complete


# ── Sandbox ────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_sandbox_blocks_rm():
    from clob.sandbox import PermissionLevel, Sandbox

    r = await Sandbox(PermissionLevel.SAFE).run("rm -rf /")
    assert r.blocked


@pytest.mark.asyncio
async def test_sandbox_allows_echo():
    from clob.sandbox import PermissionLevel, Sandbox

    r = await Sandbox(PermissionLevel.SAFE).run("echo clob test")
    assert r.success and "clob test" in r.stdout


@pytest.mark.asyncio
async def test_sandbox_log():
    from clob.sandbox import PermissionLevel, Sandbox

    sb = Sandbox(PermissionLevel.SAFE)
    await sb.run("echo one")
    await sb.run("rm -rf /")
    log = sb.execution_log()
    assert len(log) == 2 and log[0].success and log[1].blocked


# ── Themes ─────────────────────────────────────────────────
def test_theme_list():
    from clob.themes import list_themes

    themes = list_themes()
    for name in ("dark", "light", "cyberpunk", "nord"):
        assert name in themes


def test_theme_get():
    from clob.themes import get_theme

    t = get_theme("dark")
    assert "Screen" in t.tcss


def test_theme_fallback():
    from clob.themes import get_theme

    assert get_theme("nonexistent-xyz").name == "dark"


# ── Attachments ────────────────────────────────────────────
def test_attachment_text(tmp_path):
    from clob.attachments import load_attachment

    f = tmp_path / "code.py"
    f.write_text("print('clob')")
    att = load_attachment(f)
    assert att.is_text and not att.is_image
    part = att.to_openai_content_part()
    assert "clob" in part["text"]


def test_attachment_messages_empty():
    from clob.attachments import attachments_to_messages

    msgs = attachments_to_messages("hello", [])
    assert msgs[0]["content"] == "hello"


# ── Image renderer ─────────────────────────────────────────
def test_image_protocol_detection():
    from clob.rendering.images import TerminalCapability

    assert TerminalCapability.detect() in ("kitty", "iterm", "sixel", "ascii")


@pytest.mark.asyncio
async def test_image_missing_file():
    from clob.rendering.images import ImageRenderer

    r = await ImageRenderer(protocol="ascii").render("/tmp/no_such_file_clob.png")
    assert "not found" in r.lower()
