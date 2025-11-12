# Scripts Directory

This directory is intended for plugin scripts that are referenced by commands.

## Email Search Script

The `search-emails` command expects to find `read_emails.py` in one of the following locations (checked in this order):

1. **Plugin scripts directory** (highest priority): `${CLAUDE_PLUGIN_ROOT}/scripts/read_emails.py`
   - This is the recommended location: `plugins/tools/scripts/read_emails.py`

2. **Claude marketplace installation**: `$HOME/.claude/plugins/marketplaces/cc_mp/plugins/tools/scripts/read_emails.py`
   - This path is used when the plugin is installed via Claude marketplace

## Setup Instructions

To use the email search functionality, ensure `read_emails.py` exists in one of the above locations. The recommended location is within this scripts directory for better portability.

The command will automatically detect and use the first available location, making it work across different environments and installation methods.