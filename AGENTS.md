# Agent Architecture

clob includes a foundational agent system designed for extensibility toward autonomous AI coding and multi-step workflows.

---

## Overview

Agents are specialized AI workflows that go beyond single-turn chat. They can:

- Plan multi-step tasks
- Execute tools (shell, filesystem, git)
- Generate and apply code patches
- Chain multiple AI calls
- Maintain execution context across steps

---

## Current Agents

### BaseAgent

All agents inherit from `BaseAgent`:

```python
class BaseAgent:
    name: str = "base"

    def __init__(self, runtime) -> None:
        self.runtime = runtime

    async def run(self, task: str, **kwargs) -> AsyncIterator[str]:
        raise NotImplementedError
```

### CoderAgent

Specialized for code generation and editing.

```python
from clob.agents.coder import CoderAgent

agent = CoderAgent(runtime)
async for token in agent.run("Write a Python quicksort implementation"):
    print(token, end="", flush=True)
```

The coder agent uses a specialized system prompt that:
- Always wraps code in markdown fences with language tags
- Explains what the code does
- Lists dependencies
- Follows language best practices

---

## Planned Agents (Roadmap)

### PlannerAgent

Breaks complex tasks into subtasks:

```
Task: "Refactor this module to use async/await"
→ Step 1: Analyze existing code
→ Step 2: Identify blocking calls
→ Step 3: Generate async version
→ Step 4: Write tests
→ Step 5: Verify changes
```

### ExecutorAgent

Executes plans step-by-step with tool calls:

```python
# Planned API
async for step in executor.run(plan):
    print(f"[{step.status}] {step.description}")
    if step.requires_approval:
        approved = await confirm(step.command)
```

### GitAgent

Understands git context:
- Reads current diff
- Understands commit history
- Generates commit messages
- Creates branches for changes

---

## Tool System

Agents use tools to interact with the environment:

### Available Tools

| Tool | Module | Description |
|------|--------|-------------|
| Shell | `clob.tools.shell` | Execute shell commands (sandboxed) |
| Filesystem | `clob.tools.filesystem` | Read/write files |
| Git | `clob.tools.git_tools` | Git operations |
| Python Exec | `clob.tools.python_exec` | Execute Python snippets |

### Using Tools in Agents

```python
from clob.sandbox import Sandbox, PermissionLevel
from clob.tools.shell import run_shell

class MyAgent(BaseAgent):
    async def run(self, task: str, **kwargs):
        sandbox = Sandbox(permission=PermissionLevel.RESTRICTED)
        
        # Run a safe command
        result = await sandbox.run("git diff --stat")
        context = f"Current git diff:\n{result.stdout}"
        
        # Send context + task to AI
        async for chunk in self.runtime.stream_response(f"{context}\n\n{task}"):
            if chunk.delta:
                yield chunk.delta
```

---

## Sandbox Permissions

Agents must specify a permission level for tool execution:

| Level | Allowed Commands | Use Case |
|-------|-----------------|----------|
| `SAFE` | Read-only: ls, cat, git status, grep | Exploration agents |
| `RESTRICTED` | Dev tools: pytest, pip, make, git | Coding agents |
| `FULL` | All commands | Advanced agents (requires explicit consent) |

```python
from clob.sandbox import Sandbox, PermissionLevel

# Default: safe
sandbox = Sandbox()

# Coding agent: restricted
sandbox = Sandbox(permission=PermissionLevel.RESTRICTED)

# Full access: user must explicitly enable
sandbox = Sandbox(permission=PermissionLevel.FULL)
```

---

## Writing a Custom Agent

```python
from clob.agents import BaseAgent
from clob.sandbox import Sandbox, PermissionLevel
from typing import AsyncIterator

class ReviewAgent(BaseAgent):
    """Code review agent — reads files and provides feedback."""
    
    name = "reviewer"
    
    SYSTEM_PROMPT = """You are an expert code reviewer.
Analyze code for: correctness, style, performance, security.
Be specific and actionable in your feedback.
"""

    async def run(self, task: str, **kwargs) -> AsyncIterator[str]:
        from clob.providers.base import ChatMessage
        
        provider = self.runtime.registry.get(self.runtime.provider)
        if not provider:
            yield "No provider configured."
            return
        
        messages = [
            ChatMessage(role="system", content=self.SYSTEM_PROMPT),
            ChatMessage(role="user", content=task),
        ]
        
        async for chunk in provider.stream_chat(
            messages, model=self.runtime.model, **kwargs
        ):
            if chunk.delta:
                yield chunk.delta
```

---

## MCP-Ready Design

The agent and tool system is architected to support future MCP (Model Context Protocol) integration:

```python
# Future: MCP tool registration (not yet implemented)
class ToolRegistry:
    """Abstract registry — will support MCP servers."""
    
    def register(self, tool: BaseTool) -> None: ...
    def register_mcp_server(self, url: str) -> None: ...  # future
    async def call(self, name: str, **kwargs) -> Any: ...
```

When MCP support is added, agents will be able to use external MCP servers as tool providers without code changes.

---

## Agent Configuration

Agents can be configured via the runtime:

```python
runtime.set_provider("openrouter")
runtime.set_model("anthropic/claude-sonnet-4")

agent = CoderAgent(runtime)
```

Or via environment:

```bash
CLOB_PROVIDER=groq CLOB_MODEL=llama3-70b-8192 clob chat "write a sorting algorithm"
```

---

## Roadmap

- [ ] PlannerAgent with multi-step task decomposition
- [ ] ExecutorAgent with step-by-step approval flow
- [ ] GitAgent with commit/branch awareness
- [ ] Multi-agent coordination
- [ ] Agent memory persistence
- [ ] MCP server integration
- [ ] Agent marketplace / plugin agents
