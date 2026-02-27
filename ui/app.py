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

import os  # reliable path to assets
import tkinter as tk
from tkinter import ttk
import controller  # You should only call the controller

MS_SplashTime = 3000  # 3 seconds
teamRows = 15  # number of roster rows (0-14)


class EntryScreen(tk.Frame):
    def __init__(self, parent, startGame=None):
        super().__init__(parent, bg="black")
        self.startGame = startGame

        # Store local roster data for display
        self.redRoster = []
        self.greenRoster = []

        # Keep track of which Player IDs have been used in this specific game
        self.notNewPlayerID = set()

        self.playerInDB = False
        self.codenameForDB = None  # Stores the codename from the database when a player is found
        # NOTE: codenameChanged is intentionally removed.
        # Per the database rules, existing players are always used as-is.
        # The codename field is read-only when a player is found in the DB.
        # -------------------------------------------------------------------
        # Input validation + entry/reset helpers are defined below __init__.
        # See: _validatePlayerID(), _validateEquipmentID(), _clearEntryFields()
        # -------------------------------------------------------------------

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
        # NOTE: No KeyRelease binding here. Existing players use their DB codename as-is.

        # Equipment ID
        tk.Label(
            controlsArea, text="Equipment ID:", fg="white", bg="black", font=("Arial", 10, "bold")
        ).grid(row=0, column=6, padx=6, pady=4, sticky="e")
        self.entryEquipID = ttk.Entry(controlsArea, width=10)
        self.entryEquipID.grid(row=0, column=7, padx=6, pady=4, sticky="w")

        # Add Player button
        addButton = ttk.Button(controlsArea, text="Add Player", command=self.addPlayerOn)
        addButton.grid(row=0, column=8, padx=10, pady=4)

        # Status label
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

    # ------------------------------------------------------------------
    # Input validation helpers
    # ------------------------------------------------------------------

    def _validatePlayerID(self, raw):
        """
        Validate the Player ID field.

        Args:
            raw (str): The raw string from the Player ID entry widget.

        Returns:
            tuple: (int, None)       if valid — the parsed integer and no error
                   (None, str)       if invalid — None and an error message string
        """
        raw = raw.strip()
        if not raw:
            return None, "Player ID cannot be empty."
        try:
            value = int(raw)
        except ValueError:
            return None, "Player ID must be a whole number."
        if value <= 0:
            return None, "Player ID must be a positive number."
        return value, None

    def _validateEquipmentID(self, raw):
        """
        Validate the Equipment ID field.

        Args:
            raw (str): The raw string from the Equipment ID entry widget.

        Returns:
            tuple: (int, None)       if valid — the parsed integer and no error
                   (None, str)       if invalid — None and an error message string
        """
        raw = raw.strip()
        if not raw:
            return None, "Equipment ID cannot be empty."
        try:
            value = int(raw)
        except ValueError:
            return None, "Equipment ID must be a whole number."
        if value <= 0:
            return None, "Equipment ID must be a positive number."
        return value, None

    # ------------------------------------------------------------------
    # Entry / reset helpers
    # ------------------------------------------------------------------

    def _clearEntryFields(self):
        """
        Full reset of all entry fields and all player lookup state flags.

        Call this after a successful Add Player, after F12, and whenever
        the entry area needs to go back to a clean blank state.

        Resets:
            - playerInDB flag
            - codenameForDB cached value
            - Player ID, Codename, and Equipment ID input widgets
            - Codename field state back to normal/editable
            - Status message cleared
        """
        self.playerInDB = False
        self.codenameForDB = None
        self.entryPlayerID.delete(0, "end")
        self.entryForCodename.configure(state="normal")
        self.entryForCodename.delete(0, "end")
        self.entryEquipID.delete(0, "end")
        self.statusVariable.set("")

    def _resetCodenameField(self):
        """
        Partial reset — clears only the codename field and lookup flags.

        Use this specifically inside on_playerID_changed when a lookup
        fails or returns an error, so only the codename area is wiped
        without touching Player ID or Equipment ID (the user may still
        be correcting just the Player ID).
        """
        self.playerInDB = False
        self.codenameForDB = None
        self.entryForCodename.configure(state="normal")
        self.entryForCodename.delete(0, "end")

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

            # Display-only
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

    def on_playerID_changed(self, event=None):
        """
        Called when the player ID field loses focus or Enter is pressed.
        Validates the Player ID, checks for duplicate session entries,
        then looks up the player in the database and fills the codename.

        If the player is found in the DB:
            - Codename field is filled with the existing value and locked (read-only).
            - Existing data is used as-is. No updates are ever made.
        If the player is not in the DB:
            - Codename field is left blank and editable for a new entry.
        """
        raw = self.entryPlayerID.get().strip()

        # Empty field — just reset quietly
        if raw == "":
            self._resetCodenameField()
            self.statusVariable.set("")
            return

        # Validate using the helper — catches empty, non-integer, and non-positive inputs
        playerID, error = self._validatePlayerID(raw)
        if error:
            self._resetCodenameField()
            self.statusVariable.set(error)
            return

        # Block if this Player ID is already in the current game session roster
        if playerID in self.notNewPlayerID:
            self._resetCodenameField()
            self.statusVariable.set(
                f"Player ID {playerID} is already in this game session. "
                "Use F12 to clear and start over."
            )
            return

        # Look up player in the database via the controller
        status, codename = controller.dbGetCodename(playerID)

        if status == "found":
            # Player exists — fill codename and lock the field (use as-is, no updates)
            self.playerInDB = True
            self.codenameForDB = codename
            # Must be "normal" before delete/insert, then lock to "readonly" after
            self.entryForCodename.configure(state="normal")
            self.entryForCodename.delete(0, "end")
            self.entryForCodename.configure(state="normal")  # force normal before insert
            self.entryForCodename.insert(0, codename)
            self.entryForCodename.configure(state="readonly")
            self.statusVariable.set(
                f"Player {playerID} found: '{codename}'. Codename will be used as-is."
            )

        elif status == "not_found":
            # New player — leave codename blank and editable
            self.playerInDB = False
            self.codenameForDB = None
            self.entryForCodename.configure(state="normal")
            self.entryForCodename.delete(0, "end")
            self.statusVariable.set("New player — enter a codename to add to the database.")
            self.entryForCodename.focus_set()

        elif status == "db_error":
            self._resetCodenameField()
            self.statusVariable.set("Database error! Check PostgreSQL connection.")

        else:
            self._resetCodenameField()
            self.statusVariable.set(f"Unknown database status: {status}")

    def addPlayerOn(self):
        """
        Unified Add Player button. Handles two scenarios only:

        1. Player EXISTS in DB → codename field was locked/filled automatically.
           Use the existing codename as-is. No DB update is made.

        2. Player does NOT exist in DB → insert new player with the entered codename.

        Duplicate Player IDs within the same game session are blocked.
        """
        team = self.teamVariable.get().strip().upper()

        # Validate Player ID using helper
        playerID, error = self._validatePlayerID(self.entryPlayerID.get())
        if error:
            self.statusVariable.set(error)
            return

        # Validate Equipment ID using helper
        equipmentID, error = self._validateEquipmentID(self.entryEquipID.get())
        if error:
            self.statusVariable.set(error)
            return

        # Block duplicate Player IDs in the same game session
        if playerID in self.notNewPlayerID:
            self.statusVariable.set(
                f"Player ID {playerID} is already in this game session. "
                "Clear the game (F12) to start over."
            )
            return

        # Get codename from UI
        codenameOfUse = self.entryForCodename.get().strip()
        if not codenameOfUse:
            self.statusVariable.set("Please enter a codename.")
            return

        # Check roster capacity
        roster = self.redRoster if team == "RED" else self.greenRoster
        if len(roster) >= teamRows:
            self.statusVariable.set(f"{team} team is full ({teamRows} players).")
            return

        if self.playerInDB:
            # Scenario 1: Player exists in DB — use codename as-is, no DB call needed
            self.statusVariable.set(
                f"Using existing codename '{codenameOfUse}' for Player {playerID}."
            )

        else:
            # Scenario 2: New player — insert into DB
            status = controller.dbInsertPlayer(playerID, codenameOfUse)

            if status == "success":
                self.statusVariable.set(
                    f"New player '{codenameOfUse}' added to database."
                )
            elif status == "duplicate":
                # Race condition: another session inserted between lookup and add
                self.statusVariable.set(
                    f"Player {playerID} already exists in the database. "
                    "Re-enter the Player ID to load their codename."
                )
                self._resetCodenameField()
                return
            else:  # "db_error"
                self.statusVariable.set("Database error — player was not saved.")
                return

        # Add to controller team list (UDP broadcast handled inside controller)
        try:
            controller.addPlayerToTeam(team, playerID, codenameOfUse, equipmentID)
        except Exception as e:
            self.statusVariable.set(f"Controller error: {e}")
            return

        # Add to local roster display
        roster.append((playerID, codenameOfUse, equipmentID))

        # Mark this Player ID as used in this game session
        self.notNewPlayerID.add(playerID)

        self.refreshTables()

        # Use _clearEntryFields to reset all inputs and flags in one call
        self._clearEntryFields()

        # Focus back to player ID for quick entry
        self.entryPlayerID.focus_set()

    def on_f1(self):
        self.statusVariable.set("Already on Entry screen.")

    def on_f12(self):
        """F12: clear controller state and reset the UI."""
        controller.clearItAll()
        self.redRoster.clear()
        self.greenRoster.clear()
        self.notNewPlayerID.clear()
        self.refreshTables()

        # Use _clearEntryFields to reset all inputs and flags in one call
        self._clearEntryFields()

        self.statusVariable.set("Cleared all entries.")

    def on_f5(self):
        try:
            controller.changePhase("ACTION")
        except Exception as e:
            self.statusVariable.set(f"changePhase not ready: {e}")

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


# main.py should call this function
def startApp():
    root = tk.Tk()
    root.title("Team One's Photon Laser Tag")

    # Hide the window at first so the user doesn't see the ugly first draw in the VM
    root.withdraw()

    def forceWinGeo():
        root.update_idletasks()
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()

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

    # IP configuration
    ttk.Label(footer, text="Network IP:").pack(side=tk.LEFT, padx=6, pady=6)

    ip_entry = ttk.Entry(footer, width=20)
    ip_entry.pack(side=tk.LEFT, padx=6, pady=6)
    ip_entry.insert(0, "127.0.0.1")

    def clickSetIP():
        controller.netSetIp(ip_entry.get().strip())

    ttk.Button(footer, text="Set Network IP", command=clickSetIP).pack(side=tk.LEFT, padx=6, pady=6)

    presentScreen = {"screen": None}

    def show_screen(new_screen):
        old = presentScreen["screen"]
        if old is not None:
            old.pack_forget()
            old.destroy()

        presentScreen["screen"] = new_screen
        new_screen.pack(in_=content, fill="both", expand=True)

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
    assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
    logo_path = os.path.normpath(os.path.join(assets_dir, "logo.png"))

    try:
        logo_img = tk.PhotoImage(file=logo_path)
        logo_img = logo_img.subsample(5, 5)
        splashPic.configure(image=logo_img, text="")
        splashPic.image = logo_img  # keep reference
    except Exception:
        splashPic.configure(text="Photon Laser Tag\nSplash Screen")

    # After 3 seconds, go to Entry screen
    def goToBegin():
        splashFrame.destroy()

        def goToAction():
            def backToEntry():
                entry = EntryScreen(content, startGame=goToAction)
                show_screen(entry)
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

        root.after_idle(build_entry)

    root.after(MS_SplashTime, goToBegin)
    root.after(MS_SplashTime + 300, controller.netBeginUDP_Listener)

    root.after(0, forceWinGeo)
    root.after(120, forceWinGeo)
    root.after(350, forceWinGeo)
    root.deiconify()

    root.mainloop()
