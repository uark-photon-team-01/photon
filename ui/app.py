"""
The Sprint 2 requirements for this file are the following:
- Splash screen for at about 3 seconds (the logo is in provided in Jim's repo)
- Then switch to Player Entry screen
- F12 clears all entries (it will call the controller)
- F5 starts game (switch to action screen later)
- Simplified to ONE button: Add Player handles all scenarios
- NEW: Track used Player IDs to prevent duplicates in the same game session

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

import os # reliable path to assets
import tkinter as tk
from tkinter import ttk
import controller  # You should only call the controller 

MS_SplashTime = 3000  # 3 seconds
teamRows = 15 # number of roster rows (0-14)

class EntryScreen(tk.Frame):
    def __init__(self, parent, startGame=None):
        super().__init__(parent, bg="black")
        self.startGame = startGame

        # store local roster data for display 
        self.redRoster = []
        self.greenRoster = []

        # Keep track of which Player IDs have been used in this specific game 
        self.notNewPlayerID = set()

        self.playerInDB = False
        self.codenameForDB = None #stores the codename from the database when a player is found.
        self.codenameChanged = False  # Track if the user changed the codename

        # Top Title Area
        titleFrame = tk.Frame(self, bg="black")
        titleFrame.pack(fill="x", pady=(10, 0))

        tk.Label(
            titleFrame,
            text="Entry Terminal",
            fg="white",
            bg="black",
            font=("Times New Roman", 16, "bold")
        ).pack()

        tk.Label(
            titleFrame,
            text="Edit Current Game",
            fg="#4a6cff",
            bg="black",
            font=("Times New Roman", 18, "bold")
        ).pack(pady=(3, 10))

        # Middle Teams Area
        teamsFrame = tk.Frame(self, bg="black")
        teamsFrame.pack(pady=5)

        # Build the two tables
        self.redRos = self.makeTeamRos(
            teamsFrame,
            teamName="RED TEAM",
            header_bg="#5a0000",
            outline="#5a0000"
        )
        self.greenRos = self.makeTeamRos(
            teamsFrame,
            teamName="GREEN TEAM",
            header_bg="#004d00",
            outline="#004d00"
        )

        self.redRos["frame"].grid(row=0, column=0, padx=20)
        self.greenRos["frame"].grid(row=0, column=1, padx=20)


        # Entry Controls Area 
        controlsArea = tk.Frame(self, bg="black")
        controlsArea.pack(fill="x", pady=(10, 5))

        # Team selection
        tk.Label(
            controlsArea, text="Team:", fg="white", bg="black", font=("Arial", 10, "bold")
        ).grid(row=0, column=0, padx=6, pady=4, sticky="e")

        self.teamVariable = tk.StringVar(value="RED")
        team_box = ttk.Combobox(
            controlsArea,
            textvariable=self.teamVariable,
            values=["RED", "GREEN"],
            width=8,
            state="readonly"
        )
        team_box.grid(row=0, column=1, padx=6, pady=4, sticky="w")

        # Player ID
        tk.Label(
            controlsArea, text="Player ID:", fg="white", bg="black", font=("Arial", 10, "bold")
        ).grid(row=0, column=2, padx=6, pady=4, sticky="e")
        self.entryPlayerID = ttk.Entry(controlsArea, width=10)
        self.entryPlayerID.grid(row=0, column=3, padx=6, pady=4, sticky="w")
        self.entryPlayerID.bind("<FocusOut>", self.on_playerID_changed)
        self.entryPlayerID.bind("<Return>", self.on_playerID_changed)

        # Codename
        tk.Label(
            controlsArea, text="Codename:", fg="white", bg="black", font=("Arial", 10, "bold")
        ).grid(row=0, column=4, padx=6, pady=4, sticky="e")
        self.entryForCodename = ttk.Entry(controlsArea, width=18)
        self.entryForCodename.grid(row=0, column=5, padx=6, pady=4, sticky="w")
        # Track when codename is manually changed
        self.entryForCodename.bind("<KeyRelease>", self.codenameHasChanged)

        # Equipment ID
        tk.Label(
            controlsArea, text="Equipment ID:", fg="white", bg="black", font=("Arial", 10, "bold")
        ).grid(row=0, column=6, padx=6, pady=4, sticky="e")
        self.entryEquipID = ttk.Entry(controlsArea, width=10)
        self.entryEquipID.grid(row=0, column=7, padx=6, pady=4, sticky="w")

        # Add Player button
        addButton = ttk.Button(controlsArea, text="Add Player", command=self.addPlayerOn)
        addButton.grid(row=0, column=8, padx=10, pady=4)

        # Error status label
        self.statusVariable = tk.StringVar(value="")
        tk.Label(
            controlsArea,
            textvariable=self.statusVariable,
            fg="yellow",
            bg="black",
            font=("Arial", 10)
        ).grid(row=1, column=0, columnspan=10, padx=6, pady=(2, 0), sticky="w")


        # Bottom Button Bar 
        buttons_frame = tk.Frame(self, bg="black")
        buttons_frame.pack(fill="x", pady=(10, 0))

        # F5 and F12
        self.keyButton(buttons_frame, "F1\nEntry", self.on_f1).pack(side="left", padx=6)
        self.keyButton(buttons_frame, "F3\nStart Game", self.on_f5).pack(side="left", padx=6)
        self.keyButton(buttons_frame, "F5\nStart Game", self.on_f5).pack(side="left", padx=6)
        self.keyButton(buttons_frame, "F12\nClear Game", self.on_f12).pack(side="right", padx=6)


        # Footer hint
        tk.Label(
            self,
            text="<F12> to Clear Game <F5> to Start Game",
            fg="white",
            bg="black",
            font=("Arial", 10)
        ).pack(fill="x", pady=(8, 10))

        # Initial paint
        self.after_idle(self.refreshTables)

    def makeTeamRos(self, parent, teamName, header_bg, outline):
        """
        Build a table-like panel with 15 rows. Each row has:
        index label, playerID display, codename display.
        """
        panel = tk.Frame(parent, bg="black")

        header = tk.Label(
            panel,
            text=teamName,
            fg="white",
            bg=header_bg,
            font=("Arial", 10, "bold"),
            width=24
        )
        header.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 5))

        rows = []
        for i in range(teamRows):
            idx = tk.Label(panel, text=str(i), fg="white", bg="black", width=2)
            idx.grid(row=i + 1, column=0, padx=(0, 6), sticky="w")

            playerBox = tk.Entry(
                panel,
                width=10,
                justify="center",
                highlightthickness=1,
                highlightbackground=outline
            )
            playerBox.grid(row=i + 1, column=1, padx=(0, 6), pady=1)

            codeBox = tk.Entry(
                panel,
                width=18,
                justify="center",
                highlightthickness=1,
                highlightbackground=outline
            )
            codeBox.grid(row=i + 1, column=2, pady=1)

            # This is the Display-only look to disable them
            playerBox.configure(state="disabled")
            codeBox.configure(state="disabled")

            rows.append((playerBox, codeBox))

        return {"frame": panel, "rows": rows}

    def keyButton(self, parent, text, cmd):
        return tk.Button(
            parent,
            text=text,
            command=cmd,
            fg="lime",
            bg="black",
            width=12,
            height=3,
            relief="raised",
            bd=2,
            font=("Arial", 9, "bold")
        )

    def codenameHasChanged(self, event=None):
     #pay attention to when a user changes the codename
        if self.playerInDB and self.codenameForDB:
            presentText = self.entryForCodename.get().strip()
            # If the text is different from codename in the database, then its time to update it
            if presentText != self.codenameForDB:
                self.codenameChanged = True
            else:
                self.codenameChanged = False

    def on_playerID_changed(self, event=None):
        """This is called when the player ID field changes and a player will be looked up in the database"""
        raw = self.entryPlayerID.get().strip()

        # Reset behavior if empty
        if raw == "":
            self.playerInDB = False
            self.codenameForDB = None
            self.codenameChanged = False
            self.entryForCodename.configure(state="normal")
            self.entryForCodename.delete(0, "end")
            self.statusVariable.set("")
            return

        # Validate playerID is an int
        try:
            playerID = int(raw)
        except ValueError:
            self.playerInDB = False
            self.codenameForDB = None
            self.codenameChanged = False
            self.entryForCodename.configure(state="normal")
            self.entryForCodename.delete(0, "end")
            self.statusVariable.set("Player ID must be an integer.")
            return

        # If ID is already in the game, just give the player the option to edit so there can be updates
        if playerID in self.notNewPlayerID:
            self.statusVariable.set(f" This game already has the following Player ID {playerID}. Edit the codename and click Add Player to update.")

        # Ask controller for codename with the NEW STATUS CODES!!!!!!!!!
        try:
            status, codenameForDB = controller.dbGetCodename(playerID)
            
            if status == "found" and codenameForDB:
                # Player exists in database 
                self.playerInDB = True
                self.codenameForDB = codenameForDB
                self.codenameChanged = False
              
                self.entryForCodename.configure(state="normal")  
                self.entryForCodename.delete(0, "end")
                self.entryForCodename.insert(0, codenameForDB)
              
                # Show the player message but the user can modify it if they want
                self.statusVariable.set(f" Player {playerID} found: '{codenameForDB}'. You can edit the name to update it.")
                
            elif status == "not_found":
                # Player not in database
                self.playerInDB = False
                self.codenameForDB = None
                self.codenameChanged = False
                self.entryForCodename.configure(state="normal")
                self.entryForCodename.delete(0, "end")
                self.statusVariable.set("New player - enter codename to add to database.")
                self.entryForCodename.focus_set()
                
            elif status == "db_error":
                # A Database error has occurred
                self.playerInDB = False
                self.codenameForDB = None
                self.codenameChanged = False
                self.entryForCodename.configure(state="normal")
                self.entryForCodename.delete(0, "end")
                self.statusVariable.set("Database error! Check PostgreSQL connection.")
                
            else:
                # Unknown status
                self.playerInDB = False
                self.codenameForDB = None
                self.codenameChanged = False
                self.entryForCodename.configure(state="normal")
                self.entryForCodename.delete(0, "end")
                self.statusVariable.set(f"The database status is unknown: {status}")
                
        except Exception as e:
            # Unexpected error
            self.playerInDB = False
            self.codenameForDB = None
            self.codenameChanged = False
            self.entryForCodename.configure(state="normal")
            self.entryForCodename.delete(0, "end")
            self.statusVariable.set(f"Error: {e}")


    def addPlayerOn(self):
        """
        Unified Add Player button that handles three scenarios:
        1. Player exists, codename NOT modified → Use existing codename (no DB update)
        2. Player exists, codename WAS modified → Update codename in DB
        3. Player doesn't exist → Insert new player into DB
        
      Also prevents duplicate Player IDs in the same game session
        """
        team = self.teamVariable.get().strip().upper()

        # Validate ints
        try:
            playerID = int(self.entryPlayerID.get().strip())
        except ValueError:
            self.statusVariable.set("Player ID must be an integer.")
            return

        try:
            equipmentID = int(self.entryEquipID.get().strip())
        except ValueError:
            self.statusVariable.set("Equipment ID must be an integer.")
            return

        # Get current codename from UI
        codenameOfUse = self.entryForCodename.get().strip()
        if not codenameOfUse:
            self.statusVariable.set("Please enter a codename.")
            return

        # If player is in the game roster, then update it
        if playerID in self.notNewPlayerID:
            try:
                status = controller.dbUpdatePlayer(playerID, codenameOfUse)
                if status != "success":
                    self.statusVariable.set(f"Player {playerID} could not be updated in the database")
                    return
            except Exception as e:
                self.statusVariable.set(f"There was an error updating: {e}")
                return
        
            # here the codename is updated in the roster
            updated = False
            for i, (playID, code, eq) in enumerate(self.redRoster):
                if playID == playerID:
                    self.redRoster[i] = (playID, codenameOfUse, eq)  # equipment ID does not change
                    updated = True
                    break
            
            if not updated:
                for i, (playID, code, eq) in enumerate(self.greenRoster):
                    if playID == playerID:
                        self.greenRoster[i] = (playID, codenameOfUse, eq)  # equipment ID does not change
                        updated = True
                        break
            
            self.refreshTables()
            self.statusVariable.set(
                f"The codename was updated for Player {playerID}. "
                "To change Player ID or Equipment ID, please delete and re-add the player."
            )
        
            # clear the inputs
            self.entryPlayerID.delete(0, "end")
            self.entryForCodename.delete(0, "end")
            self.entryEquipID.delete(0, "end")
            self.playerInDB = False
            self.codenameForDB = None
            self.codenameChanged = False
            self.entryPlayerID.focus_set()
            return

        # Update UI roster
        roster = self.redRoster if team == "RED" else self.greenRoster
        if len(roster) >= teamRows:
            self.statusVariable.set(f"{team} team is full ({teamRows} players).")
            return

        # Scenario 1 & 2: Player exists in database
        if self.playerInDB:
            # Check if codename was changed
            if self.codenameChanged and codenameOfUse != self.codenameForDB:
                # Scenario 2: Update the codename in database
                try:
                    status = controller.dbUpdatePlayer(playerID, codenameOfUse)
                    
                    if status == "success":
                        self.statusVariable.set(f" Updated Player {playerID} to '{codenameOfUse}'")
                    elif status == "not_found":
                        self.statusVariable.set(f" Player {playerID} was not found. Therefore, no update")
                        return
                    else:  # db_error
                        self.statusVariable.set(f" Database error - update failed")
                        return
                except Exception as e:
                    self.statusVariable.set(f"Error updating: {e}")
                    return
            else:
                # Scenario 1: Use the existing codename 
                self.statusVariable.set(f" Using existing codename '{codenameOfUse}' for Player {playerID}")

        # Scenario 3: Player doesn't exist . Then, insert a new player
        else:
            try:
                status = controller.dbInsertPlayer(playerID, codenameOfUse)
                
                if status == "success":
                    self.statusVariable.set(f" New player '{codenameOfUse}' added to database")
                elif status == "duplicate":
                    # This shouldn't happen since we check self.playerInDB above
                    self.statusVariable.set(f" Player {playerID} already exists in database")
                    return
                else:  # db_error
                    self.statusVariable.set(f" Database error - player not saved")
                    return
            except Exception as e:
                self.statusVariable.set(f"Error inserting: {e}")
                return

        # Add to controller team list (broadcast handled inside controller)
        try:
            controller.addPlayerToTeam(team, playerID, codenameOfUse, equipmentID)
        except Exception as e:
            self.statusVariable.set(f"Controller error: {e}")
            return

        # Add to local roster for display
        roster.append((playerID, codenameOfUse, equipmentID))
        
        # NEW: Mark this Player ID as used in this game session
        self.notNewPlayerID.add(playerID)
        
        self.refreshTables()

        # Clear inputs for next entry
        self.entryPlayerID.delete(0, "end")
        self.entryForCodename.delete(0, "end")
        self.entryEquipID.delete(0, "end")

        # Reset flags for next entry
        self.playerInDB = False
        self.codenameForDB = None
        self.codenameChanged = False

        # Focus back to player ID for quick entry
        self.entryPlayerID.focus_set()

    def on_f1(self):
        # Placeholder for later 
        self.statusVariable.set("Already on Entry screen.")

    def on_f12(self):
        """F12 behavior: clear controller state and refresh UI."""
        controller.clearItAll()
        self.redRoster.clear()
        self.greenRoster.clear()
        
        # NEW: Clear the used Player IDs set
        self.notNewPlayerID.clear()
        
        self.refreshTables()
        self.statusVariable.set("Cleared all entries.")

        #this avoids stale lookup
        self.playerInDB = False
        self.codenameForDB = None
        self.codenameChanged = False
        
        self.entryPlayerID.delete(0, "end")
        self.entryForCodename.delete(0, "end")
        self.entryEquipID.delete(0, "end")

    def on_f5(self):
        try:
            controller.changePhase("ACTION")
        except Exception as e:
            self.statusVariable.set(f"changePhase not ready: {e}")

        # Switch what user sees
        if self.startGame:
            self.startGame()
        else:
            self.statusVariable.set("Game started (action screen later).")

    def refreshTables(self):
        """Paint roster data into the 15-row tables."""
        self._paint_roster(self.redRos["rows"], self.redRoster)
        self._paint_roster(self.greenRos["rows"], self.greenRoster)

    def _paint_roster(self, ui_rows, roster):
        for i in range(teamRows):
            playerBox, codeBox = ui_rows[i]

            playerBox.configure(state="normal")
            codeBox.configure(state="normal")

            playerBox.delete(0, "end")
            codeBox.delete(0, "end")

            if i < len(roster):
                playerID, codename, equipmentID = roster[i]
                playerBox.insert(0, str(playerID))
                codeBox.insert(0, codename)

            playerBox.configure(state="disabled")
            codeBox.configure(state="disabled")

class ActionScreen(tk.Frame):
    def __init__(self, parent, on_return_entry=None):
        super().__init__(parent, bg="black")
        self.on_return_entry = on_return_entry

        tk.Label(
            self,
            text="GAME ACTION SCREEN (just a placeholder)",
            fg="white",
            bg="black",
            font=("Times New Roman", 28, "bold")
        ).pack(pady=40)

        tk.Label(
            self,
            text="Press F1 to return to Entry",
            fg="white",
            bg="black",
            font=("Arial", 14)
        ).pack()

    def on_f1(self):
        if self.on_return_entry:
            self.on_return_entry()

#the main.py should call this function
def startApp():
    root = tk.Tk()
    root.title("Team One's Photon Laser Tag")

    # this hides the  window  at first so user doesn't see ugly first draw in VM
    root.withdraw()

    def forceWinGeo():
        root.update_idletasks()
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()

        # Fit to VM display so the active window is not partially off-screen
        w = min(1100, sw - 40)
        h = min(760, sh - 80)
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)

        root.geometry(f"{w}x{h}+{x}+{y}")
        root.minsize(980, 680)

    content = tk.Frame(root, bg="black")
    content.pack(side="top", fill="both", expand=True)

    footer = tk.Frame(root, bg="black")
    footer.pack(side="bottom", fill="x")

    #Ip configuration
    ttk.Label(footer, text="Network IP:").pack(side=tk.LEFT, padx=6, pady=6)

    ip_entry = ttk.Entry(footer, width=20)
    ip_entry.pack(side=tk.LEFT, padx=6, pady=6)
    ip_entry.insert(0, "127.0.0.1")

    def clickSetIP():
        controller.netSetIp(ip_entry.get().strip())

    ttk.Button(footer, text="Set Network IP", command=clickSetIP).pack(side=tk.LEFT, padx=6, pady=6)

    # keybinds 
    presentScreen = {"screen": None}

    def show_screen(new_screen):
        old = presentScreen["screen"]
        if old is not None:
            old.pack_forget()
            old.destroy()
    
        presentScreen["screen"] = new_screen
        new_screen.pack(in_=content, fill="both", expand=True)
    
        # This forces the new layout & redraw in the Virtual Machine 
        root.update_idletasks()
        root.after_idle(new_screen.update_idletasks)

    
    def f12Clear(event):
        if presentScreen["screen"] is not None and hasattr(presentScreen["screen"], "on_f12"):
            presentScreen["screen"].on_f12()
        else:
            controller.clearItAll()

    def f5Start(event):
        if presentScreen["screen"] is not None and hasattr(presentScreen["screen"], "on_f5"):
            presentScreen["screen"].on_f5()

    def f1Entry(event):
        if presentScreen["screen"] is not None and hasattr(presentScreen["screen"], "on_f1"):
            presentScreen["screen"].on_f1()

    def f3Start(event):
        # Just a Placeholder: same behavior as F5 for now
        if presentScreen["screen"] is not None and hasattr(presentScreen["screen"], "on_f5"):
            presentScreen["screen"].on_f5()

    root.bind("<F1>", f1Entry)
    root.bind("<F3>", f3Start)
    root.bind("<F12>", f12Clear)
    root.bind("<F5>", f5Start)

    # Splash screen 
    splashFrame = tk.Frame(content, bg="black")
    splashFrame.pack(fill="both", expand=True)

    splashPic = tk.Label(
        splashFrame,
        text="",
        fg="white",
        bg="black",
        font=("Times New Roman", 28, "bold")
    )
    splashPic.pack(expand=True)

    # Try to load Jim's logo from assets/logo.png
    # If it fails (missing file or png unsupported), fall back to text.
    assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
    logo_path = os.path.join(assets_dir, "logo.png")
    logo_path = os.path.normpath(logo_path)

    logo_img = None
    try:
        logo_img = tk.PhotoImage(file=logo_path)

        scale = 5
        logo_img = logo_img.subsample(scale, scale)

        splashPic.configure(image=logo_img, text="")
        splashPic.image = logo_img  # keep reference
    except Exception:
        splashPic.configure(text="Photon Laser Tag\nSplash Screen")

    # After 3 seconds, go to Entry/Beginning screen 
    def goToBegin():
        splashFrame.destroy()

        def goToAction():
            def backToEntry():
                entry = EntryScreen(content, startGame=goToAction)
                show_screen(entry)
                # just reapply the geometry after the switch back
                root.after(0, forceWinGeo)
                root.after(120, forceWinGeo)
              
            show_screen(ActionScreen(content, on_return_entry=backToEntry))
            root.after(0, forceWinGeo)
            root.after(120, forceWinGeo)

        def build_entry():
            entry = EntryScreen(content, startGame=goToAction)
            show_screen(entry)
            root.after(0, forceWinGeo)
            root.after(120, forceWinGeo)

        # After Tk finishes the event loop cycle the entry will be built
        root.after_idle(build_entry)

    root.after(MS_SplashTime, goToBegin)

    # The listener starts after the splash/entry render path begins
    root.after(MS_SplashTime + 300, controller.netBeginUDP_Listener)

    # the geometry is applied multiple times and aftwerwards the window is shown
    root.after(0, forceWinGeo)
    root.after(120, forceWinGeo)
    root.after(350, forceWinGeo)
    root.deiconify()

    root.mainloop()
