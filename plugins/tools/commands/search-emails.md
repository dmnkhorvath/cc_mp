Search emails in Office 365/Outlook using the Microsoft Graph API.

The user wants to search for emails with the following query: {{args}}

Instructions:
1. Parse the search query and any options from the arguments
2. Use the Bash tool to execute the email search. Try these approaches in order:
   a. First attempt: Check if script exists at "${CLAUDE_PLUGIN_ROOT}/scripts/read_emails.py"
   b. Second attempt: Check if script exists at "$HOME/.claude/plugins/marketplaces/cc_mp/plugins/tools/scripts/read_emails.py"
   c. If none exist, inform the user about the location issue
3. ALWAYS use --format json by default for structured output
4. Support these search patterns:
   - Simple search: Just the search term (searches in both subject and body)
   - Subject search: If user mentions "subject", use --search-in subject
   - Body search: If user mentions "body", use --search-in body
   - Count: If a number is mentioned, use it for --count (max 50)
   - Text: If "text" or "readable" is mentioned, use --format text (override default JSON)
   - Full: If "full" or "complete" is mentioned, use --full-body

Examples of how to interpret arguments:
- "invoice" → --search "invoice" --format json
- "meeting subject" → --search "meeting" --search-in subject --format json
- "report body 20" → --search "report" --search-in body --count 20 --format json
- "urgent text" → --search "urgent" --format text
- "budget full" → --search "budget" --full-body --format json

Implementation approach for script location:
1. First check if the script exists within the plugin at "${CLAUDE_PLUGIN_ROOT}/scripts/read_emails.py"
2. If not found, check marketplace installation at "$HOME/.claude/plugins/marketplaces/cc_mp/plugins/tools/scripts/read_emails.py"
3. Use whichever path exists, or report error if neither exists

Example execution flow:
```bash
# Check for script in plugin scripts directory (primary location)
if [ -f "${CLAUDE_PLUGIN_ROOT}/scripts/read_emails.py" ]; then
    uv run python "${CLAUDE_PLUGIN_ROOT}/scripts/read_emails.py" [options]
# Check for script in Claude marketplace installation
elif [ -f "$HOME/.claude/plugins/marketplaces/cc_mp/plugins/tools/scripts/read_emails.py" ]; then
    uv run python "$HOME/.claude/plugins/marketplaces/cc_mp/plugins/tools/scripts/read_emails.py" [options]
else
    echo "Error: read_emails.py not found in expected locations:"
    echo "  - ${CLAUDE_PLUGIN_ROOT}/scripts/read_emails.py"
    echo "  - $HOME/.claude/plugins/marketplaces/cc_mp/plugins/tools/scripts/read_emails.py"
    echo ""
    echo "Please ensure read_emails.py is placed in the plugin's scripts directory."
fi
```

Execute the search and display the results to the user. If no results are found, let the user know.

Default behavior:
- Searches in both subject and body
- Returns 10 results
- JSON format output (structured data)