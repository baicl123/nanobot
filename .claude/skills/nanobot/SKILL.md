# nanobot Development Patterns

> Auto-generated skill from repository analysis

## Overview

The nanobot repository is a Python-based agent system built around a core agent loop with modular tools and context management. The codebase follows clean architecture principles with clear separation between agent logic, configuration, and tools. Development patterns focus on iterative enhancement of the core agent loop, robust context handling, and maintaining clean code through regular refactoring cycles.

## Coding Conventions

### File Naming
- Use `snake_case` for all Python files
- Test files follow `test_*.py` pattern
- Tools are organized in `nanobot/agent/tools/` directory

### Import Style
```python
# Use relative imports within the nanobot package
from ..context import ContextManager
from .tools import ToolRegistry
```

### Export Style
```python
# Use named exports in __init__.py
from .loop import AgentLoop
from .context import ContextManager

__all__ = ['AgentLoop', 'ContextManager']
```

### Commit Messages
- Use conventional commit format: `type: description`
- Common prefixes: `fix:`, `feat:`, `refactor:`, `docs:`, `style:`
- Keep messages around 63 characters
- Examples:
  - `feat: add prompt caching to context system`
  - `fix: resolve agent loop termination issue`
  - `refactor: simplify tool registration logic`

## Workflows

### PR Merge with Refactor
**Trigger:** When a PR is merged and needs code cleanup or simplification
**Command:** `/merge-and-refactor`

1. Merge the PR with original implementation
2. Immediately refactor merged code to simplify/optimize
3. Update related files in `nanobot/agent/tools/`
4. Update corresponding tests in `tests/test_*.py`
5. Commit refactored changes with descriptive message

```python
# Example: After merging a tool addition, refactor for consistency
class NewTool(BaseTool):
    def execute(self, context):
        # Refactor to match existing tool patterns
        return self._process_with_context(context)
```

### Remote Merge Sync
**Trigger:** When working on a feature branch that needs latest main changes
**Command:** `/sync-main`

1. Fetch latest changes: `git fetch origin`
2. Merge remote main: `git merge origin/main`
3. Resolve any conflicts in:
   - `nanobot/` directory files
   - `tests/` directory
   - `README.md`
   - `pyproject.toml`
4. Continue with feature development

### Agent Loop Enhancement
**Trigger:** When adding new capabilities or fixing bugs in the core agent logic
**Command:** `/enhance-agent`

1. Modify `nanobot/agent/loop.py` with new functionality
2. Update related tools in `nanobot/agent/tools/*.py` if needed
3. Add corresponding tests in `tests/test_*.py`
4. Update `README.md` with usage examples
5. Test the complete agent workflow

```python
# Example enhancement pattern
class AgentLoop:
    def run(self, context):
        # Add new enhancement while preserving existing flow
        if self._should_use_new_feature(context):
            return self._enhanced_execution(context)
        return self._standard_execution(context)
```

### Version Release
**Trigger:** When preparing a new version release
**Command:** `/release-version`

1. Update version in `nanobot/__init__.py`:
   ```python
   __version__ = "0.2.0"
   ```
2. Update version in `pyproject.toml`:
   ```toml
   [tool.poetry]
   version = "0.2.0"
   ```
3. Update `README.md` with release notes and new features
4. Commit with message: `chore: bump version to 0.2.0`

### Context System Update
**Trigger:** When enhancing prompt caching, context handling, or system prompts
**Command:** `/update-context`

1. Modify `nanobot/agent/context.py` with new context features
2. Update or add tests in `tests/test_context_prompt_cache.py`
3. Ensure prompt cache compatibility
4. Test context persistence and retrieval

```python
# Example context enhancement
class ContextManager:
    def cache_prompt(self, prompt, cache_key):
        # Implement or enhance caching logic
        if cache_key in self.cache:
            return self._merge_cached_context(prompt, cache_key)
        return self._create_new_context(prompt, cache_key)
```

### Config Schema Update
**Trigger:** When adding new configuration options or modifying existing ones
**Command:** `/update-config`

1. Modify `nanobot/config/schema.py` with new configuration fields
2. Update `README.md` with documentation for new config options
3. Test configuration validation and default values
4. Ensure backward compatibility

```python
# Example config schema addition
class ConfigSchema:
    new_feature_enabled: bool = False
    new_feature_options: Dict[str, Any] = field(default_factory=dict)
```

## Testing Patterns

- Tests follow the pattern `test_*.py`
- Focus on testing agent loop functionality and context management
- Include specific tests for prompt caching: `test_context_prompt_cache.py`
- Test configuration changes thoroughly
- Maintain test coverage for core agent functionality

```python
# Example test pattern
def test_agent_loop_enhancement():
    agent = AgentLoop()
    context = create_test_context()
    result = agent.run(context)
    assert result.success
    assert result.output_contains_expected_data()
```

## Commands

| Command | Purpose |
|---------|---------|
| `/merge-and-refactor` | Merge PR and immediately clean up/optimize the code |
| `/sync-main` | Merge latest main branch changes into feature branch |
| `/enhance-agent` | Add new features or fixes to the core agent loop |
| `/release-version` | Prepare and commit a new version release |
| `/update-context` | Modify context system with caching and prompt handling |
| `/update-config` | Add or modify configuration schema and documentation |