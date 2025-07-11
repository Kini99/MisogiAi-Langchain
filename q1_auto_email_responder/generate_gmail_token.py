#!/usr/bin/env python3
"""
Gmail OAuth 2.0 Refresh Token Generator

This script helps you generate a refresh token for Gmail API access.
You'll need your Google Cloud OAuth 2.0 client ID and client secret.

Usage:
    python generate_gmail_token.py
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Gmail API scopes required by the application
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

def get_client_config():
    """Get OAuth client configuration from user input."""
    print("=== Gmail OAuth 2.0 Refresh Token Generator ===\n")
    
    client_id = input("Enter your Google Cloud OAuth 2.0 Client ID: ").strip()
    client_secret = input("Enter your Google Cloud OAuth 2.0 Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("Error: Client ID and Client Secret are required!")
        return None
    
    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"]
        }
    }

def generate_refresh_token():
    """Generate refresh token using OAuth 2.0 flow."""
    try:
        # Get client configuration
        client_config = get_client_config()
        if not client_config:
            return
        
        print("\n=== Starting OAuth 2.0 Flow ===\n")
        print("1. A browser window will open for Google authentication")
        print("2. Sign in with your Google account")
        print("3. Grant permissions for Gmail access")
        print("4. You'll be redirected to localhost (this is normal)\n")
        
        # Create OAuth flow
        flow = InstalledAppFlow.from_client_config(
            client_config,
            SCOPES
        )
        
        # Run the OAuth flow
        credentials = flow.run_local_server(
            port=0,
            prompt='consent',
            access_type='offline'
        )
        
        # Display the refresh token
        print("\n=== SUCCESS! Your Refresh Token ===\n")
        print("=" * 50)
        print(credentials.refresh_token)
        print("=" * 50)
        
        print("\n=== Next Steps ===\n")
        print("1. Copy the refresh token above")
        print("2. Add it to your .env file:")
        print("   GMAIL_REFRESH_TOKEN=your_refresh_token_here")
        print("3. Also add your client ID and secret:")
        print("   GMAIL_CLIENT_ID=your_client_id")
        print("   GMAIL_CLIENT_SECRET=your_client_secret")
        
        # Test the credentials
        print("\n=== Testing Credentials ===\n")
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            print("✓ Credentials refreshed successfully")
        
        print("✓ Refresh token generated successfully!")
        print("✓ You can now use this token with the email response system")
        
    except Exception as e:
        print(f"\n❌ Error generating refresh token: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure your Client ID and Client Secret are correct")
        print("2. Ensure you have enabled Gmail API in Google Cloud Console")
        print("3. Check that your OAuth consent screen is configured")
        print("4. Try running the script again")

if __name__ == "__main__":
    generate_refresh_token() 