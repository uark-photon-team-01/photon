"""
The Sprint 2 requirements for this file are the following:
- Splash screen for at about 3 seconds (the logo is in provided in Jim's repo)
- Then switch to Player Entry screen
- F12 clears all entries (it will call the controller)
- F5 starts game (switch to action screen later)
- Simplified to ONE button: Add Player handles all scenarios
- Track used Player IDs to prevent duplicates in the same game session

Sprint 3 additions:
- Real ActionScreen replacing the placeholder
- Countdown timer: start sequence → 30-second warning → 6-minute game clock
- Red and green team scoreboards populated from entry screen roster
- Play-by-play event log panel

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

import os
import tkinter as tk
from tkinter import ttk
import controller

MS_SplashTime = 3000  # 3 seconds
teamRows = 15         # number of roster rows (0-14)

# Game timing constants
GAME_SECONDS      = 360   # 6 minutes full game clock
WARNING_SECONDS   = 30    # 30-second warning threshold
START_COUNTDOWN   = 5     # 5-second start countdown sequence


# =============================================================================
# EntryScreen
# =============================================================================

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
        self.codenameForDB = None
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

        tk.Label(
            controlsArea, text="Player ID:", fg="white", bg="black", font=("Arial", 10, "bold")
        ).grid(row=0, column=2, padx=6, pady=4, sticky="e")
        self.entryPlayerID = ttk.Entry(controlsArea, width=10)
        self.entryPlayerID.grid(row=0, column=3, padx=6, pady=4, sticky="w")
        self.entryPlayerID.bind("<FocusOut>", self.on_playerID_changed)
        self.entryPlayerID.bind("<Return>", self.on_playerID_changed)

        tk.Label(
            controlsArea, text="Codename:", fg="white", bg="black", font=("Arial", 10, "bold")
        ).grid(row=0, column=4, padx=6, pady=4, sticky="e")
        self.entryForCodename = ttk.Entry(controlsArea, width=18)
        self.entryForCodename.grid(row=0, column=5, padx=6, pady=4, sticky="w")
        # NOTE: No KeyRelease binding. Existing players use their DB codename as-is.

        tk.Label(
            controlsArea, text="Equipment ID:", fg="white", bg="black", font=("Arial", 10, "bold")
        ).grid(row=0, column=6, padx=6, pady=4, sticky="e")
        self.entryEquipID = ttk.Entry(controlsArea, width=10)
        self.entryEquipID.grid(row=0, column=7, padx=6, pady=4, sticky="w")

        addButton = ttk.Button(controlsArea, text="Add Player", command=self.addPlayerOn)
        addButton.grid(row=0, column=8, padx=10, pady=4)

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

        tk.Label(
            self,
            text="<F12> to Clear Game <F5> to Start Game",
            fg="white",
            bg="black",
            font=("Arial", 10)
        ).pack(fill="x", pady=(8, 10))

        self.after_idle(self.refreshTables)

    # ------------------------------------------------------------------
    # Input validation helpers
    # ------------------------------------------------------------------

    def _validatePlayerID(self, raw):
        """
        Validate the Player ID field.

        Returns:
            tuple: (int, None)  if valid
                   (None, str)  if invalid — None and an error message
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

        Returns:
            tuple: (int, None)  if valid
                   (None, str)  if invalid — None and an error message
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
        Use inside on_playerID_changed when a lookup fails or errors,
        without touching Player ID or Equipment ID.
        """
        self.playerInDB = False
        self.codenameForDB = None
        self.entryForCodename.configure(state="normal")
        self.entryForCodename.delete(0, "end")

    def makeTeamRos(self, parent, teamName, header_bg, outline):
        """Build a table-like panel with 15 rows."""
        panel = tk.Frame(parent, bg="black")

        tk.Label(
            panel,
            text=teamName,
            fg="white",
            bg=header_bg,
            font=("Arial", 10, "bold"),
            width=24
        ).grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 5))

        rows = []
        for i in range(teamRows):
            tk.Label(panel, text=str(i), fg="white", bg="black", width=2).grid(
                row=i + 1, column=0, padx=(0, 6), sticky="w"
            )

            playerBox = tk.Entry(
                panel, width=10, justify="center",
                highlightthickness=1, highlightbackground=outline
            )
            playerBox.grid(row=i + 1, column=1, padx=(0, 6), pady=1)

            codeBox = tk.Entry(
                panel, width=18, justify="center",
                highlightthickness=1, highlightbackground=outline
            )
            codeBox.grid(row=i + 1, column=2, pady=1)

            playerBox.configure(state="disabled")
            codeBox.configure(state="disabled")
            rows.append((playerBox, codeBox))

        return {"frame": panel, "rows": rows}

    def keyButton(self, parent, text, cmd):
        return tk.Button(
            parent, text=text, command=cmd,
            fg="lime", bg="black", width=12, height=3,
            relief="raised", bd=2, font=("Arial", 9, "bold")
        )

    def on_playerID_changed(self, event=None):
        """
        Called when the player ID field loses focus or Enter is pressed.
        Validates, checks for duplicates, then looks up in the database.
        """
        raw = self.entryPlayerID.get().strip()

        if raw == "":
            self._resetCodenameField()
            self.statusVariable.set("")
            return

        playerID, error = self._validatePlayerID(raw)
        if error:
            self._resetCodenameField()
            self.statusVariable.set(error)
            return

        if playerID in self.notNewPlayerID:
            self._resetCodenameField()
            self.statusVariable.set(
                f"Player ID {playerID} is already in this game session. "
                "Use F12 to clear and start over."
            )
            return

        status, codename = controller.dbGetCodename(playerID)

        if status == "found":
            self.playerInDB = True
            self.codenameForDB = codename
            self.entryForCodename.configure(state="normal")
            self.entryForCodename.delete(0, "end")
            self.entryForCodename.configure(state="normal")
            self.entryForCodename.insert(0, codename)
            self.entryForCodename.configure(state="readonly")
            self.statusVariable.set(
                f"Player {playerID} found: '{codename}'. Codename will be used as-is."
            )

        elif status == "not_found":
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
        Unified Add Player button. Two scenarios only:
        1. Player EXISTS in DB → use codename as-is, no DB update.
        2. Player NOT in DB    → insert new player.
        Duplicate Player IDs within the same game session are blocked.
        """
        team = self.teamVariable.get().strip().upper()

        playerID, error = self._validatePlayerID(self.entryPlayerID.get())
        if error:
            self.statusVariable.set(error)
            return

        equipmentID, error = self._validateEquipmentID(self.entryEquipID.get())
        if error:
            self.statusVariable.set(error)
            return

        if playerID in self.notNewPlayerID:
            self.statusVariable.set(
                f"Player ID {playerID} is already in this game session. "
                "Clear the game (F12) to start over."
            )
            return

        codenameOfUse = self.entryForCodename.get().strip()
        if not codenameOfUse:
            self.statusVariable.set("Please enter a codename.")
            return

        roster = self.redRoster if team == "RED" else self.greenRoster
        if len(roster) >= teamRows:
            self.statusVariable.set(f"{team} team is full ({teamRows} players).")
            return

        if self.playerInDB:
            self.statusVariable.set(
                f"Using existing codename '{codenameOfUse}' for Player {playerID}."
            )
        else:
            status = controller.dbInsertPlayer(playerID, codenameOfUse)
            if status == "success":
                self.statusVariable.set(f"New player '{codenameOfUse}' added to database.")
            elif status == "duplicate":
                self.statusVariable.set(
                    f"Player {playerID} already exists in the database. "
                    "Re-enter the Player ID to load their codename."
                )
                self._resetCodenameField()
                return
            else:
                self.statusVariable.set("Database error — player was not saved.")
                return

        try:
            controller.addPlayerToTeam(team, playerID, codenameOfUse, equipmentID)
        except Exception as e:
            self.statusVariable.set(f"Controller error: {e}")
            return

        roster.append((playerID, codenameOfUse, equipmentID))
        self.notNewPlayerID.add(playerID)
        self.refreshTables()
        self._clearEntryFields()
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
        self._clearEntryFields()
        self.statusVariable.set("Cleared all entries.")

    def on_f5(self):
        """F5: transition to the action screen."""
        controller.changePhase("ACTION")
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


# =============================================================================
# ActionScreen
# =============================================================================

class ActionScreen(tk.Frame):
    """
    Real game action screen. Sections:
      - Countdown timer at the top
      - Red team total  |  Green team total
      - Red scoreboard  |  Green scoreboard
      - Play-by-play event log at the bottom

    Timer flow:
      1. Start countdown  : 5 → 4 → 3 → 2 → 1 → GO!
      2. 30-second warning: shown when time_remaining hits WARNING_SECONDS
      3. Full game clock  : counts down from GAME_SECONDS (6 minutes)
    """

    def __init__(self, parent, on_return_entry=None):
        super().__init__(parent, bg="black")
        self.on_return_entry = on_return_entry

        # Timer state
        self._timer_job = None          # holds the after() job id so we can cancel
        self._time_remaining = GAME_SECONDS
        self._start_count = START_COUNTDOWN
        self._phase = "starting"        # "starting" | "playing" | "warning" | "done"

        self._build_layout()
        self._populate_rosters()

        # Kick off the start countdown after the screen is fully drawn
        self.after(500, self._tick_start_countdown)

    # ------------------------------------------------------------------
    # Layout builder
    # ------------------------------------------------------------------

    def _build_layout(self):
        """Build all the visual sections of the action screen."""

        # ── Top bar: timer + phase label ──────────────────────────────
        topBar = tk.Frame(self, bg="black")
        topBar.pack(fill="x", pady=(10, 0))

        self.phaseLabel = tk.Label(
            topBar,
            text="GET READY",
            fg="yellow",
            bg="black",
            font=("Arial", 14, "bold")
        )
        self.phaseLabel.pack()

        self.timerLabel = tk.Label(
            topBar,
            text=self._fmt_start(START_COUNTDOWN),
            fg="white",
            bg="black",
            font=("Arial", 48, "bold")
        )
        self.timerLabel.pack(pady=(0, 6))

        # ── Team totals row ───────────────────────────────────────────
        totalsBar = tk.Frame(self, bg="black")
        totalsBar.pack(fill="x", pady=(4, 0))

        tk.Label(
            totalsBar, text="RED TEAM TOTAL",
            fg="#ff4444", bg="black", font=("Arial", 12, "bold")
        ).grid(row=0, column=0, padx=40)

        self.redTotalLabel = tk.Label(
            totalsBar, text="0",
            fg="#ff4444", bg="black", font=("Arial", 22, "bold")
        )
        self.redTotalLabel.grid(row=1, column=0, padx=40)

        tk.Label(
            totalsBar, text="GREEN TEAM TOTAL",
            fg="#44ff44", bg="black", font=("Arial", 12, "bold")
        ).grid(row=0, column=1, padx=40)

        self.greenTotalLabel = tk.Label(
            totalsBar, text="0",
            fg="#44ff44", bg="black", font=("Arial", 22, "bold")
        )
        self.greenTotalLabel.grid(row=1, column=1, padx=40)

        totalsBar.columnconfigure(0, weight=1)
        totalsBar.columnconfigure(1, weight=1)

        # ── Scoreboards + event log ───────────────────────────────────
        middleArea = tk.Frame(self, bg="black")
        middleArea.pack(fill="both", expand=True, pady=(10, 0))

        # Red scoreboard
        redPane = tk.Frame(middleArea, bg="black")
        redPane.grid(row=0, column=0, padx=14, sticky="nsew")

        tk.Label(
            redPane, text="RED TEAM",
            fg="white", bg="#5a0000",
            font=("Arial", 10, "bold"), width=28
        ).pack(fill="x")

        self.redScoreFrame = tk.Frame(redPane, bg="black")
        self.redScoreFrame.pack(fill="both", expand=True)

        # Green scoreboard
        greenPane = tk.Frame(middleArea, bg="black")
        greenPane.grid(row=0, column=1, padx=14, sticky="nsew")

        tk.Label(
            greenPane, text="GREEN TEAM",
            fg="white", bg="#004d00",
            font=("Arial", 10, "bold"), width=28
        ).pack(fill="x")

        self.greenScoreFrame = tk.Frame(greenPane, bg="black")
        self.greenScoreFrame.pack(fill="both", expand=True)

        # Event log
        logPane = tk.Frame(middleArea, bg="black")
        logPane.grid(row=0, column=2, padx=14, sticky="nsew")

        tk.Label(
            logPane, text="PLAY BY PLAY",
            fg="white", bg="#1a1a2e",
            font=("Arial", 10, "bold"), width=34
        ).pack(fill="x")

        self.eventLog = tk.Text(
            logPane,
            bg="#0d0d1a", fg="white",
            font=("Courier", 9),
            width=36, height=20,
            state="disabled",
            wrap="word"
        )
        self.eventLog.pack(fill="both", expand=True)

        logScroll = ttk.Scrollbar(logPane, command=self.eventLog.yview)
        logScroll.pack(side="right", fill="y")
        self.eventLog.configure(yscrollcommand=logScroll.set)

        middleArea.columnconfigure(0, weight=1)
        middleArea.columnconfigure(1, weight=1)
        middleArea.columnconfigure(2, weight=2)

        # ── Bottom bar ────────────────────────────────────────────────
        bottomBar = tk.Frame(self, bg="black")
        bottomBar.pack(fill="x", pady=(8, 6))

        tk.Label(
            bottomBar,
            text="F1 — Return to Entry",
            fg="white", bg="black", font=("Arial", 10)
        ).pack()

    # ------------------------------------------------------------------
    # Roster population
    # ------------------------------------------------------------------

    def _populate_rosters(self):
        """
        Read players from the shared controller state and build scoreboard
        rows for each team. Shows codename and score (0 to start).
        """
        state = controller.grabState()

        self._build_scoreboard(self.redScoreFrame, state.redTeam, "#ff4444")
        self._build_scoreboard(self.greenScoreFrame, state.greenTeam, "#44ff44")

        # Update team totals
        self.redTotalLabel.configure(text=str(self._team_total(state.redTeam)))
        self.greenTotalLabel.configure(text=str(self._team_total(state.greenTeam)))

        # Populate event log with anything already logged
        for entry in state.eventLog:
            self._log(entry)

    def _build_scoreboard(self, frame, team, color):
        """Build one row per player in the given frame."""
        for widget in frame.winfo_children():
            widget.destroy()

        if not team:
            tk.Label(
                frame, text="No players added.",
                fg="grey", bg="black", font=("Arial", 9)
            ).pack(anchor="w", padx=6, pady=2)
            return

        for player in team:
            row = tk.Frame(frame, bg="black")
            row.pack(fill="x", padx=4, pady=1)

            tk.Label(
                row, text=player.codename,
                fg=color, bg="black",
                font=("Arial", 10, "bold"), width=18, anchor="w"
            ).pack(side="left")

            score = getattr(player, "score", 0)
            tk.Label(
                row, text=str(score),
                fg="white", bg="black",
                font=("Arial", 10), width=6, anchor="e"
            ).pack(side="right")

    def _team_total(self, team):
        """Sum all player scores for a team."""
        return sum(getattr(p, "score", 0) for p in team)

    def _log(self, message):
        """Append a line to the event log text widget."""
        self.eventLog.configure(state="normal")
        self.eventLog.insert("end", message + "\n")
        self.eventLog.see("end")
        self.eventLog.configure(state="disabled")

    # ------------------------------------------------------------------
    # Timer logic
    # ------------------------------------------------------------------

    def _fmt_start(self, count):
        """Format the start countdown display."""
        if count <= 0:
            return "GO!"
        return str(count)

    def _fmt_clock(self, seconds):
        """Format seconds as M:SS for the game clock."""
        m = seconds // 60
        s = seconds % 60
        return f"{m}:{s:02d}"

    def _tick_start_countdown(self):
        """
        Phase 1 — Start countdown: counts down from START_COUNTDOWN to GO!
        Transitions to the main game clock once GO! is shown.
        """
        if self._start_count > 0:
            self.timerLabel.configure(
                text=self._fmt_start(self._start_count),
                fg="white"
            )
            self.phaseLabel.configure(text="GET READY", fg="yellow")
            self._start_count -= 1
            self._timer_job = self.after(1000, self._tick_start_countdown)
        else:
            # Show GO! briefly then switch to game clock
            self.timerLabel.configure(text="GO!", fg="lime")
            self.phaseLabel.configure(text="GAME ON", fg="lime")
            self._log("--- GAME STARTED ---")
            self._timer_job = self.after(800, self._start_game_clock)

    def _start_game_clock(self):
        """Transition from start countdown into the main game clock."""
        self._time_remaining = GAME_SECONDS
        self._phase = "playing"
        controller.changePhase("Playing")
        self._tick_game_clock()

    def _tick_game_clock(self):
        """
        Phase 2 — Game clock: counts down from GAME_SECONDS to 0.
        Triggers the 30-second warning when time hits WARNING_SECONDS.
        """
        if self._time_remaining <= 0:
            # Game over
            self._phase = "done"
            self.timerLabel.configure(text="0:00", fg="red")
            self.phaseLabel.configure(text="GAME OVER", fg="red")
            self._log("--- GAME OVER ---")
            controller.changePhase("Done")
            return

        if self._time_remaining == WARNING_SECONDS and self._phase != "warning":
            # 30-second warning
            self._phase = "warning"
            self.phaseLabel.configure(text="⚠ 30 SECOND WARNING", fg="orange")
            self._log("--- 30 SECOND WARNING ---")

        # Update the timer display
        color = "orange" if self._phase == "warning" else "white"
        self.timerLabel.configure(
            text=self._fmt_clock(self._time_remaining),
            fg=color
        )

        # Sync time to controller state
        controller.grabState().time_remaining = self._time_remaining

        self._time_remaining -= 1
        self._timer_job = self.after(1000, self._tick_game_clock)

    def _stop_timer(self):
        """Cancel any running timer job safely."""
        if self._timer_job is not None:
            self.after_cancel(self._timer_job)
            self._timer_job = None

    # ------------------------------------------------------------------
    # Key handlers
    # ------------------------------------------------------------------

    def on_f1(self):
        """F1: stop timer and return to entry screen."""
        self._stop_timer()
        if self.on_return_entry:
            self.on_return_entry()

    def on_f12(self):
        """F12 on action screen: stop timer, let clearItAll handle state."""
        self._stop_timer()
        controller.clearItAll()


# =============================================================================
# App entry point
# =============================================================================

def startApp():
    root = tk.Tk()
    root.title("Team One's Photon Laser Tag")
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
        splashFrame, text="",
        fg="white", bg="black",
        font=("Times New Roman", 28, "bold")
    )
    splashPic.pack(expand=True)

    assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
    logo_path = os.path.normpath(os.path.join(assets_dir, "logo.png"))

    try:
        logo_img = tk.PhotoImage(file=logo_path)
        logo_img = logo_img.subsample(5, 5)
        splashPic.configure(image=logo_img, text="")
        splashPic.image = logo_img
    except Exception:
        splashPic.configure(text="Photon Laser Tag\nSplash Screen")

    def goToBegin():
        splashFrame.destroy()

        def goToAction():
            def backToEntry():
                entry = EntryScreen(content, startGame=goToAction)
                show_screen(entry)
                root.after(0, forceWinGeo)
                root.after(120, forceWinGeo)

            action = ActionScreen(content, on_return_entry=backToEntry)
            show_screen(action)
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
