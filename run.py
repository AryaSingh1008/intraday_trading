#!/usr/bin/env python3
"""
====================================================
   AI INTRADAY TRADING ASSISTANT
   Simple startup script

   Just run:  python run.py
====================================================
"""

import subprocess
import sys
import os
import webbrowser
import threading
import time


def print_banner():
    print("\n" + "=" * 60)
    print("     AI INTRADAY TRADING ASSISTANT")
    print("     Helping your family trade smarter!")
    print("=" * 60)


def install_requirements():
    """Install all required packages."""
    print("\n[STEP 1] Installing required packages...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT
        )
        print("         Packages installed successfully!")
    except subprocess.CalledProcessError:
        print("         Warning: Some packages may not have installed.")
        print("         Try manually: pip install -r requirements.txt")


def open_browser_delayed():
    """Open browser after server starts."""
    time.sleep(3)
    webbrowser.open("http://localhost:8000")
    print("\n[INFO] Browser opened at http://localhost:8000")
    print("[INFO] Press Ctrl+C to stop the application\n")


def start_server():
    """Start the FastAPI server."""
    print("\n[STEP 2] Starting the server...")
    print("         Opening browser in 3 seconds...")

    # Open browser in background thread
    t = threading.Thread(target=open_browser_delayed)
    t.daemon = True
    t.start()

    # Start uvicorn server
    import uvicorn
    uvicorn.run(
        "backend.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="warning"
    )


if __name__ == "__main__":
    print_banner()

    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    install_requirements()
    start_server()
