"""Utility to clear messaging tables (Conversation, Message).

Usage:
    python scripts/clear_messages.py        # prompts for confirmation
    python scripts/clear_messages.py --yes  # runs without prompt

This script imports the Flask app and database from the project and deletes all rows from the
Message and Conversation tables, committing the transaction.
"""
import sys
import os
import argparse

# Ensure project root is on sys.path so `app` package can be imported when running this script directly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app import create_app
from app.models import db, Conversation, Message


def confirm(prompt="Are you sure you want to DELETE ALL messages and conversations? [y/N]: "):
    try:
        resp = input(prompt)
    except EOFError:
        return False
    return resp.strip().lower() in ("y", "yes")


def main():
    parser = argparse.ArgumentParser(description="Clear messages and conversations from the database")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    if not args.yes and not confirm():
        print("Aborted.")
        return 1

    app = create_app()
    with app.app_context():
        # Delete messages first due to FK
        deleted_messages = Message.query.delete()
        deleted_convos = Conversation.query.delete()
        db.session.commit()
        print(f"Deleted {deleted_messages} messages and {deleted_convos} conversations.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
