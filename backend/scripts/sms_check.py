
"""
SMS integration check for Africa's Talking.

Usage:
    python scripts/sms_check.py +2547XXXXXXXX "Test message"

This script tests the SMS integration without requiring the full app to run.
"""

import os
import sys

# Add the backend directory to the Python path.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.services.sms_service import send_message


def main():
    if len(sys.argv) < 3:
        print('Usage: python scripts/sms_check.py <phone_number> <message>')
        print(
            'Example: python scripts/sms_check.py '
            '+254712345678 "Hello from AT"'
        )
        sys.exit(1)

    phone = sys.argv[1]
    message = sys.argv[2]

    print(f"Sending SMS to {phone}...")
    print(f"Message: {message}")
    print("-" * 50)

    success = send_message(phone, message)

    print("-" * 50)

    if success:
        print("SUCCESS: SMS sent successfully!")
    else:
        print("FAILED: SMS failed to send. Check the logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()

    sys.exit(0)