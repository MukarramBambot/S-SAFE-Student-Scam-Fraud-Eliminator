import uvicorn
import webbrowser
import threading
import time
import sys
import os

def open_browser():
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    print("Starting S-SAFE AI Backend...")
    
    # Ensure we are in the project root
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Start browser in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run Uvicorn
    try:
        uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
    except KeyboardInterrupt:
        print("\nStopping server...")
        sys.exit(0)
