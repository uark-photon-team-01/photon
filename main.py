import tkinter as tkr #built-in python library for making user windows
import sys
import os
from ui import app # Imports the app.py from the ui folder

# window = tkr.Tk() #the main window object
# window.title("Repo Skeleton Test") #This .title comes from the window object in Tkinter
# #.Label & .pack are Tkinter methods. 
# #.Label() is a widget class
# #.pack() is a layout method to place things & is a part of the Label widget object
# #padx & pady is just whitespace around the text from the edge of the window
# tkr.Label(window, text = "Hey Ya! This Repo skeleton is good to go.").pack(padx=25, pady=25)
# window.mainloop() #starts an event loop to keep the app running until a user quits.

"""
=========================================================
PHOTON LASER TAG - MAIN ENTRY POINT
=========================================================
Repository Structure:
- main.py    : Starts the app, creates the main window, and handles screen flow (splash -> entry -> game).
- install.sh : Setup script for dependencies (installs python3-tk, etc.).
- db/        : PostgreSQL database code.
- ui/        : Tkinter screen and window UI code.
- net/       : Network and UDP communication code.
- assets/    : Images and audio files.

How to Run (VM Instructions):
1. Login with student / student
2. Open Terminal Emulator:
   cd ~
   sudo apt-get update
   git clone https://github.com/uark-photon-team-01/photon.git
   cd ~/photon
   git checkout main && git fetch origin && git reset --hard origin/main && git clean -fd
   bash install.sh
   pkill -f "python3 main.py" 2>/dev/null || true
   python3 main.py

*UI RENDERING NOTE*: If widgets do not fully draw on startup, drag and resize 
the window. This forces Linux/VirtualBox to send a fresh repaint event.

Team Info:
- Centarrius Brooks (CentariB)
- Will Boone (WillBoone24)
- Emma Mahaffey (EmmaMah258)
- Caleb Carpenter (CollegeBoundCaleb)
"""

if __name__ == "__main__":
    app.startApp()
