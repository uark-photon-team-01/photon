"""
The Sprint 2 requirements for this file are the following:
- Splash screen for at about 3 seconds (the logo is in provided in Jim's repo)
- Then switch to Player Entry screen
- F12 clears all entries (it will call the controller)
- F5 starts game (switch to action screen later)

Jim's starter material will be used here.
- In Jim's repo there are assets & screen references:
  - assets/logo.jpg (splash logo)
  - entry_terminal_screen.jpg (entry screen reference)
  - game_action.jpg (action screen reference)
  - baseicon.jpg (use this later)
  - photon_tracks/ (later we will add music)

Tips!
- Build the actual Player Entry screen layout using the screenshots in Jim's repo/class slides.
- Wire buttons/inputs to the controller functions (Do not call the DB/UDP directly).
"""

import tkinter as tk
from tkinter import ttk
import controller  # You should only call the controller 

MS_SplashTime = 3000  # 3 seconds

#the main.py should call this function
def startApp():
  
    root = tk.Tk()
    root.title("Team One's Photon Laser Tag")
    root.geometry("800x550")

    # keybinds 
    # The Tkinter's bind will need a function that accepts only one parameter (the event object).
    def f12Clear(event):
        controller.clearItAll()
        # Hey Emma, be sure to also refresh the entry screen after clearing

    def f5Start(event):
        print("The game has started but will switch to the action screen later.")
        #  switch to the action screen later

    root.bind("<F12>", f12Clear) #When F12 is pressed, tkinter will call the function f12Clear
    root.bind("<F5>", f5Start)

    # Splash screen 
    splash = ttk.Label(root, text="Splash Time!", font=("Times New Roman", 28, "bold"))
    splash.pack(expand=True)

    # Emma make sure to show Jim's logo from assets/logo.jpg
    # After 3 seconds, the player should go to Entry/Beginning screen 
    def goToBegin():
        splash.destroy()

        # This is just a placeholder right now so that the repo can run.
        # Hey Emma, make sure to replace this with the real Entry screen UI.
        entry = ttk.Label(root, text="This is not the real Player Entry Screen", font=("Times New Roman", 20))
        entry.pack(expand=True)

        # IP CONFIGURATION ---
        
        # Create a container frame so they stay together
        ip_frame = ttk.Frame(root)
        ip_frame.pack(pady=20)

        # Add the label and text entry box
        ttk.Label(ip_frame, text="Network IP:").pack(side=tk.LEFT, padx=5)
        
        ip_entry = ttk.Entry(ip_frame)
        ip_entry.pack(side=tk.LEFT, padx=5)
        ip_entry.insert(0, "127.0.0.1") # Default value

        # Create the function to run when button is clicked
        def on_set_ip_click():
            # Get the text from the box
            new_ip = ip_entry.get()
            # Call the controller
            controller.netSetIp(new_ip)

        # Add the button
        ttk.Button(ip_frame, text="Set Network IP", command=on_set_ip_click).pack(side=tk.LEFT, padx=5)
        
        # ----------------------------------------

        # Here's the Sprint 2 checklist that you need to implement:
        # - team select (RED/GREEN)
        # - playerID input (int)
        # - codename display/entry (string)
        # - equipmentID input (int)
        #
        # Write code so that the database can flow through the Controller:
        # - controller.dbGetCodename(playerID)
        # - if not found: controller.dbInsertPlayer(playerID, codename)
        #
        # after the code above add:
        # - controller.addPlayerToTeam(team, playerID, codename, equipmentID)
        # - controller.netBroadcastEquipment(equipmentID)
        #
        # Here's the reference layout pic in Jim's repo: entry_terminal_screen.jpg

    root.after(MS_SplashTime, goToBegin)

    controller.netBeginUDP_Listener()

    root.mainloop()
