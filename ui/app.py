"""
Photon Laser Tag UI Application

This file handles the full front-end UI using Tkinter.

Main responsibilities:
- Splash screen → Entry screen → Action screen flow
- Player entry + validation + database interaction
- Team roster management (Red vs Green)
- Game timer, scoreboard, and event log display
- Music playback during gameplay (optional via pygame)

Works alongside:
- controller.py → handles game logic + networking + DB calls
"""

"""
=========================================================
PHOTON GAME CONTROLLER - LOGIC & STATE
=========================================================
This file acts as the central brain. The UI (app.py) calls this, 
and this calls the Database (database.py) and Network (udp.py).

SCORING & GAMEPLAY RULES:
1. Opponent Tag    : Tagger gains 10 points. Team gains 10 points.
2. Same-Team Tag   : Tagger loses 10 points. Tagged loses 10 points. 
                     Team total drops by 20 points.
3. Base Score      : Player gains 100 points and receives a [BASE] icon. 
                     Team gains 100 points.
   - Code 43 = Red Base (Green player scores)
   - Code 53 = Green Base (Red player scores)

INVALID EVENT HANDLING:
- Unknown transmitter IDs or garbage text ("hello") are ignored.
- Self-tags (e.g., 11:11) are ignored.
- Hits received before the "PLAYING" phase are ignored.
"""

import os
import glob
import random
import tkinter as tk
from tkinter import ttk
import controller
import time

try:
    import pygame
    PYGAME_OK = True
except Exception:
    PYGAME_OK = False

try:
    from PIL import Image, ImageTk
    PIL_OK = True
    print("Pillow/ImageTk loaded successfully.")
except Exception as e:
    PIL_OK = False
    print("Pillow/ImageTk import failed:", e)

# -----------------------------
# Timing & Game Configuration
# -----------------------------

MS_SplashTime = 3000
teamRows = 15

GAME_SECONDS = 360
WARNING_SECONDS = 30
WARNING_MUSIC_DELAY = 13


# =============================================================================
# EntryScreen
# =============================================================================

class EntryScreen(tk.Frame):
    """
    Entry screen where players are added before the game starts.

    Features:
    - Add players to RED or GREEN teams
    - Prevent duplicate Player IDs in same session
    - Fetch codename from DB or allow new entry
    - Validate Player ID and Equipment ID
    - Start game or clear all entries
    """
    
    def __init__(self, parent, startGame=None):
        super().__init__(parent, bg="black")
        self.startGame = startGame

        self.redRoster = []
        self.greenRoster = []
        self.notNewPlayerID = set()

        self.playerInDB = False
        self.codenameForDB = None

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

        buttons_frame = tk.Frame(self, bg="black")
        buttons_frame.pack(fill="x", pady=(10, 0))

        self.keyButton(buttons_frame, "F1\nEntry", self.on_f1).pack(side="left", padx=6)
        self.keyButton(buttons_frame, "F3\nStart Game", self.startf5).pack(side="left", padx=6)
        self.keyButton(buttons_frame, "F5\nStart Game", self.startf5).pack(side="left", padx=6)
        self.keyButton(buttons_frame, "F12\nClear Game", self.on_f12).pack(side="right", padx=6)

        tk.Label(
            self,
            text="<F12> to Clear Game    <F5> to Start Game",
            fg="white",
            bg="black",
            font=("Arial", 10)
        ).pack(fill="x", pady=(8, 10))

        self.after_idle(self.refreshTables)

    def _validatePlayerID(self, raw):
        """
        Validates Player ID input:
        - Must not be empty
        - Must be an integer
        - Must be positive
        Returns: (value, error_message)
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
        Same validation rules as Player ID but for equipment.
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

    def _clearEntryFields(self):
        self.playerInDB = False
        self.codenameForDB = None
        self.entryPlayerID.delete(0, "end")
        self.entryForCodename.configure(state="normal")
        self.entryForCodename.delete(0, "end")
        self.entryEquipID.delete(0, "end")
        self.statusVariable.set("")

    def _resetCodenameField(self):
        self.playerInDB = False
        self.codenameForDB = None
        self.entryForCodename.configure(state="normal")
        self.entryForCodename.delete(0, "end")

    def makeTeamRos(self, parent, teamName, header_bg, outline):
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
        Triggered when Player ID field loses focus or user presses Enter.
    
        Logic:
        - Validate Player ID
        - Prevent duplicates in current session
        - Query database for existing player
            → If found: autofill codename (readonly)
            → If not: allow user to enter new codename
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
                f"Player ID {playerID} is already in this game session. Use F12 to clear and start over."
            )
            return

        try:
            status, codename = controller.dbGetCodename(playerID)
        except Exception:
            self._resetCodenameField()
            self.statusVariable.set("Database error! Check PostgreSQL connection.")
            return

        if status == "found":
            self.playerInDB = True
            self.codenameForDB = codename
            self.entryForCodename.configure(state="normal")
            self.entryForCodename.delete(0, "end")
            self.entryForCodename.insert(0, codename)
            self.entryForCodename.configure(state="readonly")
            self.entryEquipID.focus_set()
            self.statusVariable.set("Player found in DB. Using existing codename.")

        elif status == "not_found":
            self.playerInDB = False
            self.codenameForDB = None
            self.entryForCodename.configure(state="normal")
            self.entryForCodename.delete(0, "end")
            self.statusVariable.set("Uh oh! Player not found, enter codename to add new player.")
            self.entryForCodename.focus_set()

        elif status == "db_error":
            self._resetCodenameField()
            self.statusVariable.set("Database error! Check PostgreSQL connection.")

        else:
            self._resetCodenameField()
            self.statusVariable.set(f"Unknown database status: {status}")

    def addPlayerOn(self):
        """
        Adds a player to the selected team.
    
        Steps:
        1. Validate Player ID and Equipment ID
        2. Ensure Player ID not already used this session
        3. Get codename (from DB or user input)
        4. Insert new player into DB if needed
        5. Add player to controller + local roster
        6. Refresh UI tables
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
                f"Player ID {playerID} is already in this game session. Clear the game (F12) to start over."
            )
            return

        codenameOfUse = self.entryForCodename.get().strip()
        if not codenameOfUse:
            self.statusVariable.set("Please enter a codename.")
            return

        if self.playerInDB:
            codenameOfUse = self.codenameForDB
        else:
            self.entryForCodename.configure(state="normal")

        roster = self.redRoster if team == "RED" else self.greenRoster
        if len(roster) >= teamRows:
            self.statusVariable.set(f"{team} team is full ({teamRows} players).")
            return

        if self.playerInDB:
            self.statusVariable.set(
                f"Using existing codename '{codenameOfUse}' for Player {playerID}."
            )
        else:
            try:
                status = controller.dbInsertPlayer(playerID, codenameOfUse)
            except Exception:
                self.statusVariable.set("Database error — player was not saved.")
                return

            if status == "success":
                self.statusVariable.set(f"New player '{codenameOfUse}' added to database.")
            elif status == "duplicate":
                self.statusVariable.set(
                    f"Player {playerID} already exists in the database. Re-enter the Player ID to load their codename."
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
        """
        Clears entire game session:
        - Calls controller to reset backend
        - Clears both team rosters
        - Resets used Player IDs
        - Clears UI fields
        """
        
        controller.clearItAll()
        self.redRoster.clear()
        self.greenRoster.clear()
        self.notNewPlayerID.clear()
        self.refreshTables()
        self._clearEntryFields()
        self.statusVariable.set("Cleared all entries.")

    def startf5(self):
        if self.startGame:
            self.startGame()
            return

        try:
            controller.startGame()
        except Exception as e:
            self.statusVariable.set(f"Unfortunately, the game could not be started. Here's why: {e}")
            return

        self.statusVariable.set("The Game has begun!")

    def refreshTables(self):
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
    Live game screen.

    Displays:
    - Game phase (Ready, Warning, Playing, Ended)
    - Countdown timer
    - Team scoreboards
    - Player scores
    - Play-by-play event log

    Also handles:
    - Music playback (optional)
    - Flashing winning team score
    - Return to Entry screen after game ends
    """
    
    def __init__(self, parent, on_return_entry=None, auto_start=False):
        super().__init__(parent, bg="black")
        self.on_return_entry = on_return_entry
        self.auto_start = auto_start

        self._refresh_job = None
        self._last_log_index = 0
        self._flash_on = False
        self._return_button_visible = False
        self.baseIconImage = None
        self.baseIconTextFallback = " [BASE]"

        self.trackFiles = []
        self._music_started = False
        self._music_file = None
        self._last_phase = None
        self._warning_music_start_at = None

        self._load_base_icon()
        self._build_layout()
        self._setup_music()

        if self.auto_start:
            controller.startGame()

        self.actionScreenUpdate()

    # ------------------------------------------------------------------
    # Assets / music
    # ------------------------------------------------------------------

    def _load_base_icon(self):
        assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
        jpg_path = os.path.normpath(os.path.join(assets_dir, "baseicon.jpg"))
    
        print("Loading base icon from:", jpg_path)
        print("JPG exists:", os.path.exists(jpg_path))
        print("PIL_OK:", PIL_OK)
    
        self.baseIconImage = None
    
        if PIL_OK and os.path.exists(jpg_path):
            try:
                img = Image.open(jpg_path)
                img = img.resize((16, 16))
                self.baseIconImage = ImageTk.PhotoImage(img)
                print("Loaded JPG base icon successfully.")
                return
            except Exception as e:
                print("Could not load JPG base icon:", e)
    
        print("Warning: Base icon could not be loaded. Using [BASE] fallback.")

    def _setup_music(self):
        """
        Loads all MP3 files from assets folder.
    
        If pygame is available:
        - Initializes audio system
        - Prepares music playback
        """
        
        self.trackFiles = []
    
        assets_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets"))
        tracks_dir = os.path.join(assets_dir, "photon_tracks")
    
        if os.path.isdir(tracks_dir):
            self.trackFiles = sorted(glob.glob(os.path.join(tracks_dir, "*.mp3")))
    
        print("PYGAME_OK =", PYGAME_OK)
        print("Found tracks:", len(self.trackFiles))
    
        if PYGAME_OK:
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                pygame.mixer.music.set_volume(1.0)
                print("pygame mixer initialized:", pygame.mixer.get_init())
            except Exception as e:
                print("pygame mixer init failed:", e)

    def _music_is_actually_playing(self):
        if not PYGAME_OK:
            return False
    
        try:
            if not pygame.mixer.get_init():
                return False
            return pygame.mixer.music.get_busy()
        except Exception as e:
            print("Music busy-check failed:", e)
            return False


    def _play_music_file(self, path, loops=0):
        if not PYGAME_OK or not path or not os.path.exists(path):
            print("Music skipped:", path)
            self._music_started = False
            self._music_file = None
            return
    
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
    
            print("Trying to play:", path)
            pygame.mixer.music.stop()
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play(loops=loops)
    
            if self._music_is_actually_playing():
                self._music_started = True
                self._music_file = path
                print("Music started and verified")
            else:
                self._music_started = False
                self._music_file = None
                print("Music play call returned, but mixer is not busy. Check VM audio output/device.")
        except Exception as e:
            self._music_started = False
            self._music_file = None
            print("Music play failed:", e)

    def _start_session_track(self):
        if not self.trackFiles:
            return
    
        if self._music_is_actually_playing():
            self._music_started = True
            return
    
        chosen_track = random.choice(self.trackFiles)
        self._play_music_file(chosen_track, loops=0)

    def _ensure_music_playing(self):
        if not self.trackFiles:
            return
    
        if self._music_is_actually_playing():
            self._music_started = True
            return
    
        print("Music is not busy during active phase; retrying track playback.")
    
        if self._music_file and os.path.exists(self._music_file):
            self._play_music_file(self._music_file, loops=0)
        else:
            self._start_session_track()

    
    def _stop_music(self):
        if PYGAME_OK:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
    
        self._music_started = False
        self._music_file = None
    
    
    def _handle_phase_audio(self, phase):
        """
        Controls music based on game phase:
    
        WARNING:
            - Wait before starting music (delayed start)
        PLAYING:
            - Ensure music is playing
        OTHER:
            - Stop music
        """
        
        now = time.monotonic()
    
        if phase != self._last_phase:
            if phase == "WARNING":
                # Delay countdown music by 13 seconds, but let timer run immediately
                self._warning_music_start_at = now + WARNING_MUSIC_DELAY
            else:
                self._warning_music_start_at = None
    
        if phase == "WARNING":
            if self._warning_music_start_at is not None and now >= self._warning_music_start_at:
                self._ensure_music_playing()
            else:
                # Make sure music does not start too early during warning
                if self._music_started or self._music_is_actually_playing():
                    self._stop_music()
    
        elif phase == "PLAYING":
            self._ensure_music_playing()
    
        else:
            if self._music_started or self._music_is_actually_playing():
                self._stop_music()
            self._warning_music_start_at = None
    
        self._last_phase = phase

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_layout(self):
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
            text="06:00",
            fg="white",
            bg="black",
            font=("Arial", 48, "bold")
        )
        self.timerLabel.pack(pady=(0, 6))

        middleArea = tk.Frame(self, bg="black")
        middleArea.pack(fill="both", expand=True, pady=(10, 0))

        redPane = tk.Frame(middleArea, bg="black")
        redPane.grid(row=0, column=0, padx=14, sticky="nsew")

        tk.Label(
            redPane, text="RED TEAM TOTAL",
            fg="#ff4444", bg="black", font=("Arial", 12, "bold")
        ).pack()

        self.redTotalLabel = tk.Label(
            redPane, text="0",
            fg="#ff4444", bg="black", font=("Arial", 22, "bold")
        )
        self.redTotalLabel.pack(pady=(0, 6))

        tk.Label(
            redPane, text="RED TEAM",
            fg="white", bg="#5a0000",
            font=("Arial", 10, "bold"), width=28
        ).pack(fill="x")

        self.redScoreFrame = tk.Frame(redPane, bg="black")
        self.redScoreFrame.pack(fill="both", expand=True)

        greenPane = tk.Frame(middleArea, bg="black")
        greenPane.grid(row=0, column=1, padx=14, sticky="nsew")

        tk.Label(
            greenPane, text="GREEN TEAM TOTAL",
            fg="#44ff44", bg="black", font=("Arial", 12, "bold")
        ).pack()

        self.greenTotalLabel = tk.Label(
            greenPane, text="0",
            fg="#44ff44", bg="black", font=("Arial", 22, "bold")
        )
        self.greenTotalLabel.pack(pady=(0, 6))

        tk.Label(
            greenPane, text="GREEN TEAM",
            fg="white", bg="#004d00",
            font=("Arial", 10, "bold"), width=28
        ).pack(fill="x")

        self.greenScoreFrame = tk.Frame(greenPane, bg="black")
        self.greenScoreFrame.pack(fill="both", expand=True)

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

        bottomBar = tk.Frame(self, bg="black")
        bottomBar.pack(fill="x", pady=(8, 6))

        tk.Label(
            bottomBar,
            text="F1 — Return to Entry",
            fg="white", bg="black", font=("Arial", 10)
        ).pack()

        self.returnButton = ttk.Button(
            bottomBar,
            text="Return to Entry",
            command=self.on_f1
        )
        # shown only when phase == ENDED

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _format_time(self, value):
        try:
            total = int(value)
        except Exception:
            try:
                return controller.formatTimeRemaining()
            except Exception:
                return "00:00"

        if total < 0:
            total = 0
        minutes = total // 60
        seconds = total % 60
        return f"{minutes:02d}:{seconds:02d}"

    def _player_has_base_icon(self, player):
        return bool(
            getattr(player, "has_baseIcon", False) or
            getattr(player, "hasbaseIcon", False)
        )

    def _sorted_roster(self, roster):
        return sorted(
            roster,
            key=lambda p: (
                -int(getattr(p, "score", 0)),
                str(getattr(p, "codename", "")).lower(),
                int(getattr(p, "playerID", 0) or getattr(p, "player_id", 0) or 0)
            )
        )

    def _show_return_button_if_needed(self, phase):
        should_show = (phase == "ENDED")
        if should_show and not self._return_button_visible:
            self.returnButton.pack(pady=6)
            self._return_button_visible = True
        elif not should_show and self._return_button_visible:
            self.returnButton.pack_forget()
            self._return_button_visible = False

    def _apply_flashing_totals(self, red_total, green_total):
        """
        Makes the winning team's score flash.
    
        If tied → no flashing
        """
        
        self._flash_on = not self._flash_on

        red_normal = "#ff4444"
        green_normal = "#44ff44"
        flash_color = "white"

        if red_total > green_total:
            self.redTotalLabel.configure(fg=flash_color if self._flash_on else red_normal)
            self.greenTotalLabel.configure(fg=green_normal)
        elif green_total > red_total:
            self.greenTotalLabel.configure(fg=flash_color if self._flash_on else green_normal)
            self.redTotalLabel.configure(fg=red_normal)
        else:
            self.redTotalLabel.configure(fg=red_normal)
            self.greenTotalLabel.configure(fg=green_normal)

    def _log(self, message):
        self.eventLog.configure(state="normal")
        self.eventLog.insert("end", message + "\n")
        self.eventLog.see("end")
        self.eventLog.configure(state="disabled")

    def logWidgetCleared(self):
        self.eventLog.configure(state="normal")
        self.eventLog.delete("1.0", "end")
        self.eventLog.configure(state="disabled")

    # ------------------------------------------------------------------
    # Live snapshot updates
    # ------------------------------------------------------------------

    def _populate_rosters(self, snapshot):
        red_roster = self._sorted_roster(snapshot.get("red_roster", []))
        green_roster = self._sorted_roster(snapshot.get("green_roster", []))

        self._build_scoreboard(self.redScoreFrame, red_roster, "#ff4444")
        self._build_scoreboard(self.greenScoreFrame, green_roster, "#44ff44")

        red_total = int(snapshot.get("red_total_score", 0))
        green_total = int(snapshot.get("green_total_score", 0))

        self.redTotalLabel.configure(text=str(red_total))
        self.greenTotalLabel.configure(text=str(green_total))
        self._apply_flashing_totals(red_total, green_total)

    def _build_scoreboard(self, frame, team, color):
        """
        Rebuilds scoreboard UI for a team.
    
        Displays:
        - Player codename
        - Player score
        - Base icon if player has it
        """
        
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

            left = tk.Frame(row, bg="black")
            left.pack(side="left", fill="x", expand=True)

            codename = str(getattr(player, "codename", "UNKNOWN"))
            
            if self._player_has_base_icon(player):
                if self.baseIconImage is not None:
                    tk.Label(
                        left,
                        image=self.baseIconImage,
                        bg="black"
                    ).pack(side="left", padx=(0, 4))
                else:
                    tk.Label(
                        left,
                        text=self.baseIconTextFallback,
                        fg="white",
                        bg="black",
                        font=("Arial", 9, "bold")
                    ).pack(side="left", padx=(0, 4))
            
            tk.Label(
                left,
                text=codename,
                fg=color,
                bg="black",
                font=("Arial", 10, "bold"),
                anchor="w"
            ).pack(side="left")


            score = int(getattr(player, "score", 0))
            tk.Label(
                row,
                text=str(score),
                fg="white",
                bg="black",
                font=("Arial", 10),
                width=6,
                anchor="e"
            ).pack(side="right")

    def phaseAndTimerUpdate(self, snapshot):
        phase = str(snapshot.get("phase", "")).upper()

        if phase == "WARNING":
            self.phaseLabel.configure(text="30 Second Warning!", fg="orange")
        elif phase == "PLAYING":
            self.phaseLabel.configure(text="Game On!", fg="lime")
        elif phase == "ENDED":
            self.phaseLabel.configure(text="Game Over!", fg="red")
        else:
            self.phaseLabel.configure(text=phase or "GET READY", fg="yellow")

        self.timerLabel.configure(
            text=self._format_time(snapshot.get("time_remaining", 0)),
            fg="white" if phase == "PLAYING"
               else "orange" if phase == "WARNING"
               else "red" if phase == "ENDED"
               else "white"
        )

        self._show_return_button_if_needed(phase)

        self._handle_phase_audio(phase)

    def eventLogUpdated(self, snapshot):
        event_log = snapshot.get("event_log", [])

        if len(event_log) < self._last_log_index:
            self.logWidgetCleared()
            self._last_log_index = 0

        new_entries = event_log[self._last_log_index:]
        for entry in new_entries:
            self._log(str(entry))

        self._last_log_index = len(event_log)

    def actionScreenUpdate(self):
        """
        Main update loop (runs every 250ms):
    
        - Updates game timer via controller
        - Gets current snapshot of game state
        - Updates:
            • Phase + timer
            • Scoreboards
            • Event log
        """
        
        controller.updateTimer()
        snapshot = controller.getActionSnapshot()

        self.phaseAndTimerUpdate(snapshot)
        self._populate_rosters(snapshot)
        self.eventLogUpdated(snapshot)

        self._refresh_job = self.after(250, self.actionScreenUpdate)

    def stopUpdateLoop(self):
        if self._refresh_job is not None:
            self.after_cancel(self._refresh_job)
            self._refresh_job = None

    # ------------------------------------------------------------------
    # Key / button handlers
    # ------------------------------------------------------------------

    def on_f1(self):
        self.stopUpdateLoop()
        self._stop_music()
        controller.clearItAll()
        self._last_log_index = 0
        if self.on_return_entry:
            self.on_return_entry()

    def on_f12(self):
        self.stopUpdateLoop()
        self._stop_music()
        controller.clearItAll()
        self._last_log_index = 0
        if self.on_return_entry:
            self.on_return_entry()


# =============================================================================
# App entry point
# =============================================================================

def startApp():
    """
    Entry point of the application.

    Flow:
    1. Show splash screen
    2. Transition to EntryScreen
    3. Start UDP listener (networking)
    4. Handle global key bindings:
        - F1 → Entry
        - F5/F3 → Start game
        - F12 → Clear game
    """
    
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

    ttk.Label(footer, text="Broadcast IP:").pack(side=tk.LEFT, padx=6, pady=6)
    ip_entry = ttk.Entry(footer, width=20)
    ip_entry.pack(side=tk.LEFT, padx=6, pady=6)
    ip_entry.insert(0, "127.0.0.1")

    def clickSetIP():
        controller.netSetIp(ip_entry.get().strip())

    ttk.Button(footer, text="Set Broadcast IP", command=clickSetIP).pack(side=tk.LEFT, padx=6, pady=6)

    presentScreen = {"screen": None}

    def show_screen(new_screen):
        old = presentScreen["screen"]
        if old is not None:
            if hasattr(old, "stopUpdateLoop"):
                old.stopUpdateLoop()
            if hasattr(old, "_stop_music"):
                old._stop_music()
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
        if presentScreen["screen"] is not None and hasattr(presentScreen["screen"], "startf5"):
            presentScreen["screen"].startf5()

    def f1Entry(event):
        if presentScreen["screen"] is not None and hasattr(presentScreen["screen"], "on_f1"):
            presentScreen["screen"].on_f1()

    def f3Start(event):
        if presentScreen["screen"] is not None and hasattr(presentScreen["screen"], "startf5"):
            presentScreen["screen"].startf5()

    root.bind("<F1>", f1Entry)
    root.bind("<F3>", f3Start)
    root.bind("<F12>", f12Clear)
    root.bind("<F5>", f5Start)

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

            action = ActionScreen(content, on_return_entry=backToEntry, auto_start=True)
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
