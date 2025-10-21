#!/usr/bin/env python3
"""
YouTubeTB - Main Entry Point

This is the main entry point for the YouTubeTB application.
It provides a unified interface to all functionality.
"""

import sys
import os
from pathlib import Path

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

