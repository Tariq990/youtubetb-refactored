#!/usr/bin/env python3
"""
YouTubeTB - Main Entry Point

This is the main entry point for the YouTubeTB application.
It provides a unified interface to all functionality.
"""

import sys
import os
from pathlib import Path

# Load environment variables early
try:
    from dotenv import load_dotenv
    
    root = Path(__file__).parent
    # Load from root .env
    if (root / ".env").exists():
        load_dotenv(dotenv_path=str(root / ".env"))
    # Load from secrets/.env (override)
    if (root / "secrets" / ".env").exists():
        load_dotenv(dotenv_path=str(root / "secrets" / ".env"))
except ImportError:
    pass  # dotenv not installed, skip

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import CLI menu
from presentation.cli.run_menu import main as run_menu  # type: ignore


def main():
    """Main entry point"""
    try:
        run_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

