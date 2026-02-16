"""
Mnexium SDK - Profile Example

Demonstrates user profile management:
- Get profile
- Update profile fields
- Delete profile fields

Run with: python profile.py
"""

import os
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False

load_dotenv()

from mnexium import Mnexium, ProviderConfig


def main():
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        print("⏭️  Skipping: OPENAI_API_KEY not set")
        return

    mnx = Mnexium(
        api_key=os.environ.get("MNX_KEY"),
        base_url=os.environ.get("MNX_BASE_URL"),
        openai=ProviderConfig(api_key=openai_key),
    )

    print("👤 Mnexium Profile Example\n")

    user = mnx.subject("profile-demo")

    # --- Get profile ---
    print("--- Get profile ---\n")

    profile = user.profile.get()
    print("Profile:", profile)

    # --- Update profile fields ---
    print("\n--- Update profile fields ---\n")

    user.profile.update([
        {"field_key": "display_name", "value": "Alice"},
        {"field_key": "timezone", "value": "America/New_York"},
        {"field_key": "language", "value": "en"},
    ])
    print("Updated: display_name, timezone, language")

    updated = user.profile.get()
    print("Updated profile:", updated)

    # --- Delete a profile field ---
    print("\n--- Delete profile field ---\n")

    user.profile.delete_field("language")
    print("Deleted: language")

    final = user.profile.get()
    print("Final profile:", final)

    print("\n✅ Profile example complete!")


if __name__ == "__main__":
    main()
