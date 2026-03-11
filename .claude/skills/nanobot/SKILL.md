# nanobot Development Patterns

> Auto-generated skill from repository analysis

## Overview

This skill teaches the development patterns for nanobot, a Python-based bot framework that integrates with various messaging platforms and AI providers. The codebase follows a modular architecture with separate components for channels (communication platforms), providers (AI/LLM integrations), CLI commands, and configuration management. Development focuses on extending platform support, enhancing AI provider integrations, and maintaining a robust command-line interface.

## Coding Conventions

### File Naming
- Use `snake_case` for all Python files
- Channel implementations: `nanobot/channels/platform_name.py`
- Provider implementations: `nanobot/providers/provider_name.py`
- Test files: `tests/test_feature_name.py`

### Import Style
```python
# Mixed import style used throughout codebase
from nanobot.config import schema
from nanobot.providers.base import BaseProvider
import asyncio
import json
```

### Export Style
- Use named exports for classes and functions
- Avoid wildcard imports

### Commit Messages
- Use conventional commit prefixes: `fix:`, `feat:`, `docs:`
- Keep messages concise (average 56 characters)
- Examples:
  ```
  fix: slack channel authentication timeout
  feat: add discord voice channel support
  docs: update provider configuration examples
  ```

## Workflows

### Channel Feature Enhancement
**Trigger:** When adding features or fixing bugs in messaging platform integrations  
**Command:** `/enhance-channel`

1. Identify the target channel implementation file in `nanobot/channels/`
2. Modify the channel-specific Python file (e.g., `nanobot/channels/slack.py`)
3. Update configuration schema if new settings are needed in `nanobot/config/schema.py`
4. Add comprehensive tests in `tests/test_*_channel.py`
5. Test the integration with the actual platform
6. Create pull request and merge after review

**Example channel implementation structure:**
```python
# nanobot/channels/slack.py
from nanobot.channels.base import BaseChannel

class SlackChannel(BaseChannel):
    def __init__(self, config):
        super().__init__(config)
        self.token = config.get('token')
    
    async def send_message(self, channel, content):
        # Implementation here
        pass
```

### CLI Command Modification
**Trigger:** When modifying command line interface functionality or default behaviors  
**Command:** `/update-cli`

1. Update CLI commands implementation in `nanobot/cli/commands.py`
2. Modify command arguments, options, or behavior as needed
3. Add or update corresponding tests in `tests/test_commands.py`
4. Test configuration integration to ensure compatibility
5. Verify backward compatibility where possible
6. Merge changes after testing

**Example CLI command structure:**
```python
# nanobot/cli/commands.py
import click

@click.command()
@click.option('--config', help='Configuration file path')
def start(config):
    """Start the nanobot service"""
    # Implementation here
    pass
```

### Merge Branch Integration
**Trigger:** When integrating feature branches or pull requests into main  
**Command:** `/merge-integration`

1. Merge main branch into feature branch to get latest changes
2. Resolve conflicts across multiple system files systematically
3. Update all affected modules in `nanobot/agent/`, `nanobot/channels/`, `nanobot/providers/`
4. Update configuration files in `nanobot/config/`
5. Ensure all tests in `tests/test_*.py` pass
6. Update documentation in `README.md` if needed
7. Perform final merge to main after all checks pass

### Documentation and Versioning
**Trigger:** When preparing releases or updating project documentation  
**Command:** `/prepare-release`

1. Update version number in `nanobot/__init__.py`:
   ```python
   __version__ = "1.2.3"
   ```
2. Update version in `pyproject.toml`:
   ```toml
   [tool.poetry]
   version = "1.2.3"
   ```
3. Update `README.md` with release notes, new features, or breaking changes
4. Update `SECURITY.md` if security-related changes were made
5. Commit all version and documentation changes
6. Tag the release appropriately

### Provider Enhancement
**Trigger:** When updating AI provider implementations or adding new provider support  
**Command:** `/update-provider`

1. Modify or create provider implementation in `nanobot/providers/`
2. Ensure the provider extends `nanobot/providers/base.py` BaseProvider class
3. Update provider registry if adding a new provider
4. Add comprehensive tests in `tests/test_*_provider.py`
5. Update base provider classes if adding common functionality
6. Test with actual provider APIs when possible

**Example provider implementation:**
```python
# nanobot/providers/openai.py
from nanobot.providers.base import BaseProvider

class OpenAIProvider(BaseProvider):
    def __init__(self, config):
        super().__init__(config)
        self.api_key = config.get('api_key')
    
    async def generate_response(self, prompt):
        # Implementation here
        pass
```

## Testing Patterns

### Test File Organization
- Test files follow pattern: `tests/test_*.py`
- Mirror the structure of the main codebase
- Group tests by functionality (channels, providers, commands)

### Test Naming
```python
# tests/test_slack_channel.py
def test_slack_message_sending():
    """Test that Slack messages are sent correctly"""
    pass

def test_slack_authentication():
    """Test Slack authentication flow"""
    pass
```

### Test Categories
- Channel integration tests
- Provider API tests  
- CLI command tests
- Configuration validation tests
- Integration tests for workflow scenarios

## Commands

| Command | Purpose |
|---------|---------|
| `/enhance-channel` | Add features or fix bugs in messaging platform integrations |
| `/update-cli` | Modify command line interface functionality |
| `/merge-integration` | Integrate feature branches with conflict resolution |
| `/prepare-release` | Update documentation and version for releases |
| `/update-provider` | Add or modify AI provider integrations |