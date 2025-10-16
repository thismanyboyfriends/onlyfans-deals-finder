#!/usr/bin/env python3
"""
Helper script to guide users through OnlyFans authentication setup
"""

import json
from pathlib import Path


def print_instructions():
    """Print detailed instructions for extracting OnlyFans credentials"""
    print("""
========================================
OnlyFans Authentication Setup
========================================

To use the OnlyFans API, you need to extract authentication credentials from your browser.

STEP 1: Open OnlyFans in your browser
--------------------------------------
1. Open Chrome, Firefox, or Edge
2. Log into OnlyFans (https://onlyfans.com)
3. Navigate to your Notifications page

STEP 2: Open Developer Tools
-----------------------------
1. Press F12 (or right-click → Inspect)
2. Click the "Network" tab
3. Click the "XHR" or "Fetch/XHR" sub-tab

STEP 3: Find the "init" request
--------------------------------
1. Refresh the page (F5)
2. Look for a request named "init" in the Network list
3. Click on it

STEP 4: Extract Required Values
--------------------------------
Click on the "Headers" tab and find these values:

REQUEST HEADERS (scroll down in Headers section):
- Cookie: Look for "sess=..." and "auth_id=..."
- User-Agent: Copy the full user agent string
- x-bc: Copy this token value

REQUIRED VALUES:
----------------
1. auth_id: From Cookie header (e.g., auth_id=12345678)
2. sess: From Cookie header (e.g., sess=abc123def456...)
3. auth_uid (OPTIONAL): Only if you have 2FA enabled (e.g., auth_uid_12345678=...)
4. user_agent: Full user agent string
5. x-bc: The x-bc token value

NOTE: The 'auth_uid' field is only present if you have two-factor authentication (2FA) enabled.
      The numbers after the underscore should match your auth_id.

========================================
""")


def collect_credentials():
    """Interactively collect credentials from user"""
    print("Please enter your OnlyFans credentials:\n")

    auth_id = input("auth_id: ").strip()
    sess = input("sess: ").strip()

    # auth_uid is optional
    print("\nDo you have 2FA (two-factor authentication) enabled? (y/n): ", end="")
    has_2fa = input().strip().lower() == 'y'

    auth_uid = ""
    if has_2fa:
        auth_uid = input("auth_uid (including the underscore and numbers): ").strip()

    user_agent = input("\nuser_agent: ").strip()
    x_bc = input("x-bc: ").strip()

    # Validate inputs
    if not all([auth_id, sess, user_agent, x_bc]):
        print("\n❌ Error: All required fields must be filled!")
        return None

    # Build auth data
    auth_data = {
        "auth_id": auth_id,
        "sess": sess,
        "user_agent": user_agent,
        "x-bc": x_bc
    }

    if auth_uid:
        auth_data["auth_uid"] = auth_uid

    return auth_data


def save_auth_file(auth_data: dict, output_path: Path):
    """Save auth data to JSON file"""
    with open(output_path, 'w') as f:
        json.dump(auth_data, f, indent=2)

    print(f"\n✅ Authentication file saved to: {output_path}")
    print("\nYou can now run the scraper!")


def main():
    """Main setup flow"""
    print_instructions()

    print("\nReady to enter your credentials? (y/n): ", end="")
    if input().strip().lower() != 'y':
        print("\nSetup cancelled. Re-run this script when you're ready.")
        return

    auth_data = collect_credentials()

    if auth_data:
        # Save to config/auth.json
        config_dir = Path(__file__).parent.parent / "config"
        config_dir.mkdir(exist_ok=True)
        output_path = config_dir / "auth.json"

        if output_path.exists():
            print(f"\n⚠️  Warning: {output_path} already exists!")
            print("Overwrite? (y/n): ", end="")
            if input().strip().lower() != 'y':
                print("\nSetup cancelled.")
                return

        save_auth_file(auth_data, output_path)

        # Security reminder
        print("\n⚠️  SECURITY REMINDER:")
        print("- Never share your auth.json file")
        print("- Add auth.json to .gitignore (already done)")
        print("- These credentials expire when you log out of OnlyFans")
        print("- Re-run this script if you get 401 authentication errors")


if __name__ == "__main__":
    main()
