# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Claude Code plugin repository that provides email integration capabilities with Microsoft Office 365/Outlook through the Microsoft Graph API. The main plugin ("Tools") includes a custom command for searching and reading emails using OAuth2 authentication.

## Key Architecture

### Plugin Structure
The project follows Claude's plugin architecture with a marketplace configuration:
- **Root marketplace config**: `.claude-plugin/marketplace.json` - Defines the cc-dominik marketplace
- **Main plugin**: `plugins/tools/` - Contains the "Tools" plugin with email functionality
- **Plugin manifest**: `plugins/tools/.claude-plugin/plugin.json` - Plugin metadata
- **Commands**: `plugins/tools/commands/search-emails.md` - Command template that dynamically locates and executes the Python script
- **Backend implementation**: `plugins/tools/scripts/read_emails.py` - Core email reader using MSAL for OAuth2

### Authentication Flow
The email functionality uses Microsoft Identity Platform with Client Credentials OAuth2:
1. Credentials stored in `plugins/tools/scripts/.env` (CLIENT_ID, CLIENT_SECRET, TENANT_ID)
2. MSAL library handles token acquisition and caching
3. Bearer tokens used for Microsoft Graph API calls

### Script Discovery Logic
The `search-emails` command template includes fallback logic for finding the Python script:
1. Primary: `${CLAUDE_PLUGIN_ROOT}/scripts/read_emails.py`
2. Fallback: `$HOME/.claude/plugins/marketplaces/cc_mp/plugins/tools/scripts/read_emails.py`

## Development Commands

### Python Environment Setup
```bash
cd plugins/tools/scripts

# Using uv (recommended):
uv pip install -e .

# Using traditional pip:
pip install -e .
```

### Testing the Email Script
```bash
cd plugins/tools/scripts

# List recent emails
python read_emails.py --list

# Search emails
python read_emails.py --search "meeting" --search-in subject --count 5

# Get full email body
python read_emails.py --search "important" --full-body --format json
```

### Managing Credentials
```bash
# Copy the example environment file
cp plugins/tools/scripts/.env.example plugins/tools/scripts/.env

# Edit .env with actual Azure AD app credentials
# Required: CLIENT_ID, CLIENT_SECRET, TENANT_ID
```

## Plugin Development

### Modifying the Plugin
When updating the plugin version after changes:
1. Update version in `plugins/tools/.claude-plugin/plugin.json`
2. Update version in `.claude-plugin/marketplace.json` if publishing
3. Update version in `plugins/tools/scripts/pyproject.toml` for Python package

### Adding New Commands
1. Create new `.md` file in `plugins/tools/commands/`
2. Use the existing `search-emails.md` as a template for script discovery logic
3. Place implementation scripts in `plugins/tools/scripts/`

### Python Dependencies
Dependencies are managed in `plugins/tools/scripts/pyproject.toml`:
- Core: `python-dotenv`, `requests`, `msal`
- Build system: `hatchling`
- Python requirement: >= 3.8

## Microsoft Graph API Integration

### API Endpoints Used
- Base: `https://graph.microsoft.com/v1.0`
- Messages: `/users/{user}/messages`
- Search: Uses `$search` and `$filter` OData parameters

### Search Capabilities
The `EmailReader` class in `read_emails.py` supports:
- Subject-only search using `$filter`
- Full-text search using `$search` (subject, body, from, to)
- Body preview filtering for relevance
- Configurable result count (1-50 emails)

### Required Azure AD Permissions
The app registration needs:
- `Mail.Read` - Application permission for reading emails
- Admin consent required for application permissions