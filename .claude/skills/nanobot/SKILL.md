# nanobot Development Patterns

> Auto-generated skill from repository analysis

## Overview

This skill teaches development patterns for **nanobot**, a Python-based chatbot framework that integrates multiple LLM providers with various communication channels (Telegram, Feishu, Matrix). The codebase emphasizes modular architecture with clear separation between providers, channels, agents, and configuration management.

## Coding Conventions

### File Naming
- Use `snake_case` for all Python files
- Group related functionality in modules: `providers/`, `channels/`, `agent/`, `config/`

### Import Style
```python
# Use relative imports within the package
from .schema import ConfigSchema
from ..providers.registry import ProviderRegistry
```

### Code Organization
```python
# Named exports pattern
class TelegramChannel:
    def __init__(self, config):
        self.config = config
    
    def send_message(self, message):
        # Implementation
        pass
```

### Commit Style
- Use conventional commit prefixes: `fix:`, `feat:`, `refactor:`, `docs:`
- Keep messages around 63 characters
- Examples: `fix: handle telegram rate limiting`, `feat: add matrix channel support`

## Workflows

### Pull Request Merge Workflow
**Trigger:** When a pull request is ready to be merged
**Command:** `/merge-pr`

1. Create implementation commit with detailed message describing the changes
2. Update relevant source files in `nanobot/providers/`, `nanobot/agent/`, or `nanobot/channels/`
3. Create merge commit referencing PR number
4. Ensure all related configuration updates are included

```bash
git commit -m "feat: implement new provider authentication method

- Add OAuth2 support for external providers
- Update provider registry to handle auth tokens
- Add configuration schema for auth settings"

git commit -m "Merge pull request #123 from feature/oauth-provider"
```

### Channel Feature Addition
**Trigger:** When adding new functionality to communication channels
**Command:** `/add-channel-feature`

1. Implement feature in the specific channel file (`feishu.py`, `telegram.py`, `matrix.py`)
2. Update `nanobot/config/schema.py` with new configuration options
3. Modify `nanobot/channels/manager.py` if channel management changes are needed
4. Create implementation commit and merge PR

```python
# Example: Adding message formatting to Telegram channel
class TelegramChannel:
    def __init__(self, config):
        self.parse_mode = config.get('parse_mode', 'HTML')  # New config option
    
    def format_message(self, text, format_type='plain'):
        if format_type == 'markdown' and self.parse_mode == 'HTML':
            return self._convert_markdown_to_html(text)
        return text
```

### Agent Loop Fixes
**Trigger:** When there are bugs or improvements needed in agent message handling
**Command:** `/fix-agent-loop`

1. Identify the issue in `nanobot/agent/loop.py`
2. Implement fix with appropriate refactoring
3. Test the agent processing flow
4. Create merge commit with clear description of the fix

```python
# Example: Fixing message processing error handling
async def process_message(self, message):
    try:
        response = await self.provider.generate_response(message)
        await self.channel.send_message(response)
    except ProviderError as e:
        # Improved error handling
        await self.channel.send_error_message(f"Provider error: {e}")
        self.logger.error(f"Provider failed: {e}")
```

### Provider Compatibility Fixes
**Trigger:** When providers have specific requirements or compatibility issues
**Command:** `/fix-provider-compatibility`

1. Identify provider-specific issue in `nanobot/providers/`
2. Implement compatibility fix in the specific provider file
3. Update `nanobot/providers/registry.py` if registry changes are needed
4. Test with the affected provider
5. Merge fix with detailed commit message

```python
# Example: Fixing LiteLLM provider streaming support
class LiteLLMProvider:
    def __init__(self, config):
        self.supports_streaming = config.get('enable_streaming', False)
    
    async def generate_response(self, prompt, stream=False):
        if stream and not self.supports_streaming:
            # Fallback to non-streaming for incompatible models
            return await self._generate_non_streaming(prompt)
        return await self._generate_streaming(prompt)
```

### Config Schema Updates
**Trigger:** When new features require configuration options
**Command:** `/add-config-option`

1. Add new configuration fields to `nanobot/config/schema.py`
2. Update related implementation files to use the new config options
3. Update documentation in `README.md` if user-facing
4. Create commit with clear description of new configuration capabilities

```python
# Example: Adding new config options to schema
CONFIG_SCHEMA = {
    "channels": {
        "telegram": {
            "token": str,
            "parse_mode": {"type": str, "default": "HTML"},  # New option
            "rate_limit": {"type": int, "default": 30}       # New option
        }
    },
    "providers": {
        "retry_attempts": {"type": int, "default": 3},       # New option
        "timeout": {"type": int, "default": 30}              # New option
    }
}
```

## Testing Patterns

Tests follow the `*.test.*` pattern, though the specific framework is not clearly defined in the repository. When writing tests:

- Create test files with descriptive names using the `*.test.*` pattern
- Test each workflow component independently
- Mock external dependencies (LLM providers, messaging APIs)
- Test error handling and edge cases

## Commands

| Command | Purpose |
|---------|---------|
| `/merge-pr` | Complete pull request merge workflow with proper commits |
| `/add-channel-feature` | Add new functionality to communication channels |
| `/fix-agent-loop` | Fix issues in the main agent processing loop |
| `/fix-provider-compatibility` | Resolve compatibility issues with LLM providers |
| `/add-config-option` | Add new configuration options and update schema |