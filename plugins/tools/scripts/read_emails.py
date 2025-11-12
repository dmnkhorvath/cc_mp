#!/usr/bin/env python3
"""
Email Reader using Microsoft Graph API with MSAL authentication.
Reads emails from Office 365/Outlook using OAuth2.
"""

import os
import sys
import argparse
import json
from datetime import datetime
from typing import Dict, List, Optional
import msal
import requests
from dotenv import load_dotenv


class EmailReader:
    """Email reader using Microsoft Graph API."""

    GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"
    SCOPES = ["https://graph.microsoft.com/.default"]

    def __init__(self):
        """Initialize the email reader with credentials from .env file."""
        load_dotenv()

        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.tenant_id = os.getenv("TENANT_ID")
        self.email_address = os.getenv("EMAIL_ADDRESS")

        self._validate_credentials()
        self.access_token = None

    def _validate_credentials(self):
        """Validate that all required credentials are present."""
        if not all([self.client_id, self.client_secret, self.tenant_id]):
            raise ValueError(
                "Missing required credentials. Please check your .env file.\n"
                "Required: CLIENT_ID, CLIENT_SECRET, TENANT_ID"
            )

    def authenticate(self) -> bool:
        """
        Authenticate using MSAL with client credentials flow.

        Returns:
            bool: True if authentication successful, False otherwise.
        """
        try:
            authority = f"https://login.microsoftonline.com/{self.tenant_id}"
            app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=authority,
                client_credential=self.client_secret
            )

            # Acquire token for application
            result = app.acquire_token_for_client(scopes=self.SCOPES)

            if "access_token" in result:
                self.access_token = result["access_token"]
                print("✓ Authentication successful")
                return True
            else:
                error = result.get("error")
                error_description = result.get("error_description")
                print(f"✗ Authentication failed: {error}")
                print(f"  Description: {error_description}")
                return False

        except Exception as e:
            print(f"✗ Authentication error: {str(e)}")
            return False

    def _make_graph_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make a request to Microsoft Graph API.

        Args:
            endpoint: The API endpoint (e.g., '/me/messages')
            params: Optional query parameters

        Returns:
            JSON response or None if request fails
        """
        if not self.access_token:
            print("✗ Not authenticated. Call authenticate() first.")
            return None

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        url = f"{self.GRAPH_API_ENDPOINT}{endpoint}"

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"✗ HTTP Error: {e}")
            if response.status_code == 401:
                print("  Token may have expired. Try authenticating again.")
            return None
        except Exception as e:
            print(f"✗ Request error: {str(e)}")
            return None

    def get_emails(self, max_count: int = 10, folder: str = "inbox") -> List[Dict]:
        """
        Retrieve emails from the specified folder.

        Args:
            max_count: Maximum number of emails to retrieve (default: 10)
            folder: Folder name (default: 'inbox')

        Returns:
            List of email dictionaries
        """
        if self.email_address:
            endpoint = f"/users/{self.email_address}/mailFolders/{folder}/messages"
        else:
            endpoint = f"/me/mailFolders/{folder}/messages"

        params = {
            "$top": max_count,
            "$select": "subject,from,receivedDateTime,bodyPreview,isRead,hasAttachments",
            "$orderby": "receivedDateTime DESC"
        }

        result = self._make_graph_request(endpoint, params)

        if result and "value" in result:
            return result["value"]
        return []

    def get_email_body(self, message_id: str) -> Optional[Dict]:
        """
        Get full email body for a specific message.

        Args:
            message_id: The ID of the message

        Returns:
            Email details with full body
        """
        if self.email_address:
            endpoint = f"/users/{self.email_address}/messages/{message_id}"
        else:
            endpoint = f"/me/messages/{message_id}"

        params = {
            "$select": "subject,from,toRecipients,receivedDateTime,body,hasAttachments"
        }

        return self._make_graph_request(endpoint, params)

    def search_emails(self, query: str, max_count: int = 10, search_in: str = "all", include_body: bool = False) -> List[Dict]:
        """
        Search for emails matching a query.

        Args:
            query: Search query string
            max_count: Maximum number of results
            search_in: Where to search - "subject", "body", or "all" (default: "all")
            include_body: If True, fetch full body content for each email (default: False)

        Returns:
            List of matching email dictionaries
        """
        if self.email_address:
            endpoint = f"/users/{self.email_address}/messages"
        else:
            endpoint = "/me/messages"

        # Construct query based on search_in parameter
        params = {
            "$top": max_count,
            "$select": "id,subject,from,toRecipients,receivedDateTime,bodyPreview,isRead,hasAttachments"
        }

        if search_in == "subject":
            # Use $filter for subject-only search
            params["$filter"] = f"contains(subject, '{query}')"
        elif search_in == "body":
            # For body search, we'll use $search with full-text and filter results manually
            # Note: Direct body filtering is limited in Graph API
            params["$search"] = f'"{query}"'
        else:  # "all"
            # Use $search for full-text search across all fields
            params["$search"] = f'"{query}"'

        result = self._make_graph_request(endpoint, params)

        if result and "value" in result:
            emails = result["value"]

            # If searching body only, filter results to only include emails with query in body
            if search_in == "body":
                filtered_emails = []
                for email in emails:
                    body_preview = email.get("bodyPreview", "").lower()
                    if query.lower() in body_preview:
                        filtered_emails.append(email)
                emails = filtered_emails

            # If include_body is True, fetch full body for each email
            if include_body:
                enriched_emails = []
                for email in emails:
                    full_email = self.get_email_body(email["id"])
                    if full_email:
                        enriched_emails.append(full_email)
                    else:
                        enriched_emails.append(email)
                return enriched_emails

            return emails
        return []

    @staticmethod
    def format_email(email: Dict) -> str:
        """
        Format an email dictionary for display.

        Args:
            email: Email dictionary from Graph API

        Returns:
            Formatted string representation
        """
        from_addr = email.get("from", {}).get("emailAddress", {})
        from_name = from_addr.get("name", "Unknown")
        from_email = from_addr.get("address", "Unknown")

        received = email.get("receivedDateTime", "")
        if received:
            dt = datetime.fromisoformat(received.replace("Z", "+00:00"))
            received = dt.strftime("%Y-%m-%d %H:%M:%S")

        subject = email.get("subject", "(No subject)")
        preview = email.get("bodyPreview", "")
        is_read = "✓" if email.get("isRead") else "✗"
        has_attachments = "📎" if email.get("hasAttachments") else ""

        output = f"""
{'=' * 80}
From: {from_name} <{from_email}>
Date: {received}
Subject: {subject}
Read: {is_read} {has_attachments}
---
{preview[:200]}{'...' if len(preview) > 200 else ''}
{'=' * 80}
"""
        return output

    @staticmethod
    def format_emails_json(emails: List[Dict]) -> str:
        """
        Format emails as JSON array.

        Args:
            emails: List of email dictionaries from Graph API

        Returns:
            JSON string representation
        """
        formatted_emails = []
        for email in emails:
            formatted_email = {
                "id": email.get("id"),
                "subject": email.get("subject"),
                "from": {
                    "name": email.get("from", {}).get("emailAddress", {}).get("name"),
                    "address": email.get("from", {}).get("emailAddress", {}).get("address")
                },
                "to": [
                    {
                        "name": recipient.get("emailAddress", {}).get("name"),
                        "address": recipient.get("emailAddress", {}).get("address")
                    }
                    for recipient in email.get("toRecipients", [])
                ],
                "receivedDateTime": email.get("receivedDateTime"),
                "isRead": email.get("isRead"),
                "hasAttachments": email.get("hasAttachments"),
                "bodyPreview": email.get("bodyPreview")
            }

            # Include full body if available
            if "body" in email:
                formatted_email["body"] = {
                    "contentType": email.get("body", {}).get("contentType"),
                    "content": email.get("body", {}).get("content")
                }

            formatted_emails.append(formatted_email)

        return json.dumps(formatted_emails, indent=2, ensure_ascii=False)


def main():
    """Main function demonstrating email reading."""
    parser = argparse.ArgumentParser(
        description="Email Reader - Microsoft Graph API with MSAL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List 10 recent emails
  python read_emails.py --list --count 10

  # Search for "invoice" in all fields
  python read_emails.py --search "invoice"

  # Search for "meeting" in subject only
  python read_emails.py --search "meeting" --search-in subject

  # Search for "report" in body only, get full body, output as JSON
  python read_emails.py --search "report" --search-in body --count 20 --full-body --format json
        """
    )

    parser.add_argument(
        "-s", "--search",
        type=str,
        help="Search query string"
    )

    parser.add_argument(
        "-i", "--search-in",
        type=str,
        choices=["subject", "body", "all"],
        default="all",
        help="Where to search: 'subject', 'body', or 'all' (default: all)"
    )

    parser.add_argument(
        "-c", "--count",
        type=int,
        default=10,
        help="Number of emails to fetch/search (default: 10, max: 50)"
    )

    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List recent emails (default if no search is specified)"
    )

    parser.add_argument(
        "-f", "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format: 'text' or 'json' (default: text)"
    )

    parser.add_argument(
        "-b", "--full-body",
        action="store_true",
        help="Fetch full email body content (slower, makes additional API calls)"
    )

    args = parser.parse_args()

    # Validate count
    args.count = min(max(1, args.count), 50)

    # Only print header if not JSON format
    if args.format != "json":
        print("Email Reader - Microsoft Graph API with MSAL\n")

    # Initialize reader
    reader = EmailReader()

    # Authenticate
    if not reader.authenticate():
        if args.format != "json":
            print("\nAuthentication failed. Please check your credentials.")
        sys.exit(1)

    # Perform action based on arguments
    if args.search:
        # Search emails
        search_location = args.search_in
        if args.format != "json":
            print(f"\nSearching for '{args.search}' in {search_location}...\n")

        emails = reader.search_emails(
            args.search,
            max_count=args.count,
            search_in=search_location,
            include_body=args.full_body
        )

        if not emails:
            if args.format == "json":
                print("[]")
            else:
                print("No matching emails found.")
            return

        if args.format != "json":
            print(f"Found {len(emails)} matching email(s):\n")

    else:
        # List recent emails (default behavior)
        if args.format != "json":
            print(f"\nFetching {args.count} recent emails from inbox...\n")
        emails = reader.get_emails(max_count=args.count)

        if not emails:
            if args.format == "json":
                print("[]")
            else:
                print("No emails found or error occurred.")
            return

        if args.format != "json":
            print(f"Found {len(emails)} email(s):\n")

    # Display results based on format
    if args.format == "json":
        print(EmailReader.format_emails_json(emails))
    else:
        for email in emails:
            print(EmailReader.format_email(email))


if __name__ == "__main__":
    main()
