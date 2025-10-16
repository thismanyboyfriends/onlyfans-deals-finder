"""
Legacy entry point for backwards compatibility.
Use 'ofscraper' command instead after installation.
"""
import sys
from cli import main

if __name__ == "__main__":
    print("Note: Consider using 'ofscraper' command after installing the package.")
    print("Run: pip install -e .")
    print()
    main()
