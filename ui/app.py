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

import os # reliable path to assets
import tkinter as tk
from tkinter import ttk
import controller  # You should only call the controller 

MS_SplashTime = 3000  # 3 seconds
TEAM_ROWS = 15 # number of roster rows (0-14)

class EntryScreen(tk.Frame):
    def __init__(self, parent, on_start_game=None):
        super().__init__(parent, bg="black")
        self.on_start_game = on_start_game

        # NEW: store local roster data for display (UI side)
        # Each entry: (player_id:int, codename:str, equipment_id:int)
        self.red_roster = []
        self.green_roster = []

        self.player_in_db = False

        # -------------------------
        # Top Title Area
        # -------------------------
        title_frame = tk.Frame(self, bg="black")
        title_frame.pack(fill="x", pady=(10, 0))

        tk.Label(
            title_frame,
            text="Entry Terminal",
            fg="white",
            bg="black",
            font=("Times New Roman", 16, "bold")
        ).pack()

        tk.Label(
            title_frame,
            text="Edit Current Game",
            fg="#4a6cff",
            bg="black",
            font=("Times New Roman", 18, "bold")
        ).pack(pady=(3, 10))

        # -------------------------
        # Middle Teams Area
        # -------------------------
        teams_frame = tk.Frame(self, bg="black")
        teams_frame.pack(pady=5)

        # Build the two tables/panels
        self.red_panel = self._build_team_panel(
            teams_frame,
            team_name="RED TEAM",
            header_bg="#5a0000",
            outline="#5a0000"
        )
        self.green_panel = self._build_team_panel(
            teams_frame,
            team_name="GREEN TEAM",
            header_bg="#004d00",
            outline="#004d00"
        )

        self.red_panel["frame"].grid(row=0, column=0, padx=20)
        self.green_panel["frame"].grid(row=0, column=1, padx=20)

        # -------------------------
        # Entry Controls Area (manual add)
        # -------------------------
        controls_frame = tk.Frame(self, bg="black")
        controls_frame.pack(fill="x", pady=(10, 5))

        # Team selection
        tk.Label(
            controls_frame, text="Team:", fg="white", bg="black", font=("Arial", 10, "bold")
        ).grid(row=0, column=0, padx=6, pady=4, sticky="e")

        self.team_var = tk.StringVar(value="RED")
        team_box = ttk.Combobox(
            controls_frame,
            textvariable=self.team_var,
            values=["RED", "GREEN"],
            width=8,
            state="readonly"
        )
        team_box.grid(row=0, column=1, padx=6, pady=4, sticky="w")

        # Player ID
        tk.Label(
            controls_frame, text="Player ID:", fg="white", bg="black", font=("Arial", 10, "bold")
        ).grid(row=0, column=2, padx=6, pady=4, sticky="e")
        self.player_id_entry = ttk.Entry(controls_frame, width=10)
        self.player_id_entry.grid(row=0, column=3, padx=6, pady=4, sticky="w")
        self.player_id_entry.bind("<FocusOut>", self.on_player_id_changed)
        self.player_id_entry.bind("<Return>", self.on_player_id_changed)

        # Codename
        tk.Label(
            controls_frame, text="Codename:", fg="white", bg="black", font=("Arial", 10, "bold")
        ).grid(row=0, column=4, padx=6, pady=4, sticky="e")
        self.codename_entry = ttk.Entry(controls_frame, width=18)
        self.codename_entry.grid(row=0, column=5, padx=6, pady=4, sticky="w")

        # Equipment ID
        tk.Label(
            controls_frame, text="Equipment ID:", fg="white", bg="black", font=("Arial", 10, "bold")
        ).grid(row=0, column=6, padx=6, pady=4, sticky="e")
        self.equipment_id_entry = ttk.Entry(controls_frame, width=10)
        self.equipment_id_entry.grid(row=0, column=7, padx=6, pady=4, sticky="w")

        # Add Player button
        add_btn = ttk.Button(controls_frame, text="Add Player", command=self.on_add_player)
        add_btn.grid(row=0, column=8, padx=10, pady=4)

        # Error/status label
        self.status_var = tk.StringVar(value="")
        tk.Label(
            controls_frame,
            textvariable=self.status_var,
            fg="yellow",
            bg="black",
            font=("Arial", 10)
        ).grid(row=1, column=0, columnspan=9, padx=6, pady=(2, 0), sticky="w")

        # -------------------------
        # Bottom Button Bar (look like F-key buttons)
        # -------------------------
        buttons_frame = tk.Frame(self, bg="black")
        buttons_frame.pack(fill="x", pady=(10, 0))

        # These buttons help visually match the screenshot.
        # Sprint 2 only strictly needs F5 and F12 behaviors.
        self._key_button(buttons_frame, "F1\nEntry", self.on_f1).pack(side="left", padx=6)
        self._key_button(buttons_frame, "F3\nStart Game", self.on_f5).pack(side="left", padx=6)
        self._key_button(buttons_frame, "F5\nStart Game", self.on_f5).pack(side="left", padx=6)
        self._key_button(buttons_frame, "F12\nClear Game", self.on_f12).pack(side="right", padx=6)


        # Footer hint
        tk.Label(
            self,
            text="<F12> to Clear Game    <F5> to Start Game",
            fg="white",
            bg="black",
            font=("Arial", 10)
        ).pack(fill="x", pady=(8, 10))

        # Initial paint
        self.refresh_tables()

    def _build_team_panel(self, parent, team_name, header_bg, outline):
        """
        Build a table-like panel with 20 rows. Each row has:
        index label, player_id display, codename display.
        """
        panel = tk.Frame(parent, bg="black")

        header = tk.Label(
            panel,
            text=team_name,
            fg="white",
            bg=header_bg,
            font=("Arial", 10, "bold"),
            width=24
        )
        header.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 5))

        rows = []
        for i in range(TEAM_ROWS):
            idx = tk.Label(panel, text=str(i), fg="white", bg="black", width=2)
            idx.grid(row=i + 1, column=0, padx=(0, 6), sticky="w")

            player_box = tk.Entry(
                panel,
                width=10,
                justify="center",
                highlightthickness=1,
                highlightbackground=outline
            )
            player_box.grid(row=i + 1, column=1, padx=(0, 6), pady=1)

            code_box = tk.Entry(
                panel,
                width=18,
                justify="center",
                highlightthickness=1,
                highlightbackground=outline
            )
            code_box.grid(row=i + 1, column=2, pady=1)

            # Display-only look: disable them
            player_box.configure(state="disabled")
            code_box.configure(state="disabled")

            rows.append((player_box, code_box))

        return {"frame": panel, "rows": rows}

    def _key_button(self, parent, text, cmd):
        """A button styled like the screenshot's function-key blocks."""
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

    def on_player_id_changed(self, event=None):
        raw = self.player_id_entry.get().strip()

        # Reset behavior if empty
        if raw == "":
            self.player_in_db = False
            self.codename_entry.configure(state="normal")
            self.codename_entry.delete(0, "end")
            self.status_var.set("")
            return

        # Validate player_id is an int
        try:
            player_id = int(raw)
        except ValueError:
            self.player_in_db = False
            self.codename_entry.configure(state="normal")
            self.codename_entry.delete(0, "end")
            self.status_var.set("Player ID must be an integer.")
            return

        # Ask controller for codename
        found = False
        db_codename = ""

        try:
            result = controller.dbGetCodename(player_id)

            # Common return patterns supported:
            # (found_bool, codename_str)
            # "codename"
            # None / "" / (False, "")
            if isinstance(result, tuple) and len(result) >= 2:
                found = bool(result[0])
                db_codename = str(result[1]) if result[1] is not None else ""
            elif isinstance(result, str):
                db_codename = result.strip()
                found = (db_codename != "")
            else:
                found = False
                db_codename = ""
        except Exception:
            found = False
            db_codename = ""

        # Only treat as found if codename is non-empty
        if found and db_codename.strip():
            self.player_in_db = True

            self.codename_entry.configure(state="normal")
            self.codename_entry.delete(0, "end")
            self.codename_entry.insert(0, db_codename)
            self.codename_entry.configure(state="disabled")

            self.status_var.set(f"YAY! Player found in DB, using codename {db_codename}")
        else:
            self.player_in_db = False

            self.codename_entry.configure(state="normal")
            self.codename_entry.delete(0, "end")

            self.status_var.set("Uh oh! Player not found. Enter codename to add new player.")
            self.codename_entry.focus_set()


    def on_add_player(self):
        team = self.team_var.get().strip().upper()

        # Validate ints
        try:
            player_id = int(self.player_id_entry.get().strip())
        except ValueError:
            self.status_var.set("Player ID must be an integer.")
            return

        try:
            equipment_id = int(self.equipment_id_entry.get().strip())
        except ValueError:
            self.status_var.set("Equipment ID must be an integer.")
            return

        # Read codename from UI (might be disabled, that's fine)
        codename_to_use = self.codename_entry.get().strip()

        # If not found in DB, require codename typed
        if not self.player_in_db and not codename_to_use:
            self.status_var.set("Uh oh! Player not found. Please enter a codename to add new player.")
            return

        # If not found in DB, insert new player
        if not self.player_in_db:
            try:
                controller.dbInsertPlayer(player_id, codename_to_use)
                self.status_var.set(f"Uh oh! Player not found. Adding new player to DB as {codename_to_use}")
            except Exception:
                # DB may not be wired yet; continue for UI demo
                pass

        # Add to controller team list (broadcast handled inside controller)
        try:
            controller.addPlayerToTeam(team, player_id, codename_to_use, equipment_id)
        except Exception as e:
            self.status_var.set(f"Controller addPlayerToTeam failed: {e}")
            return

        # Update UI roster
        roster = self.red_roster if team == "RED" else self.green_roster

        if len(roster) >= TEAM_ROWS:
            self.status_var.set(f"{team} team is full ({TEAM_ROWS} players).")
            return

        roster.append((player_id, codename_to_use, equipment_id))
        self.refresh_tables()

        # Clear inputs for next entry
        self.player_id_entry.delete(0, "end")
        self.codename_entry.configure(state="normal")  # unlock for next player
        self.codename_entry.delete(0, "end")
        self.equipment_id_entry.delete(0, "end")

        # Reset DB flag for next entry
        self.player_in_db = False

        self.status_var.set(f"Added {codename_to_use} (Player {player_id}) to {team} with Equip {equipment_id}")

    def on_f1(self):
        # Placeholder for later (already on entry screen)
        self.status_var.set("Already on Entry screen.")

    def on_f12(self):
        """F12 behavior: clear controller state and refresh UI."""
        controller.clearItAll()
        self.red_roster.clear()
        self.green_roster.clear()
        self.refresh_tables()
        self.status_var.set("Cleared all entries.")

    def on_f5(self):
        try:
            controller.changePhase("ACTION")
        except Exception as e:
            self.status_var.set(f"changePhase not ready: {e}")

        # Switch what user sees
        if self.on_start_game:
            self.on_start_game()
        else:
            self.status_var.set("Game started (action screen later).")

    def refresh_tables(self):
        """Paint roster data into the 20-row tables."""
        self._paint_roster(self.red_panel["rows"], self.red_roster)
        self._paint_roster(self.green_panel["rows"], self.green_roster)

    def _paint_roster(self, ui_rows, roster):
        for i in range(TEAM_ROWS):
            player_box, code_box = ui_rows[i]

            player_box.configure(state="normal")
            code_box.configure(state="normal")

            player_box.delete(0, "end")
            code_box.delete(0, "end")

            if i < len(roster):
                player_id, codename, equipment_id = roster[i]
                player_box.insert(0, str(player_id))
                code_box.insert(0, codename)

            player_box.configure(state="disabled")
            code_box.configure(state="disabled")

class ActionScreen(tk.Frame):
    def __init__(self, parent, on_return_entry=None):
        super().__init__(parent, bg="black")
        self.on_return_entry = on_return_entry

        tk.Label(
            self,
            text="GAME ACTION SCREEN (placeholder)",
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
    root.geometry("800x710")

    content = tk.Frame(root, bg="black")
    content.pack(side="top", fill="both", expand=True)

    footer = tk.Frame(root, bg="black")
    footer.pack(side="bottom", fill="x")

    # --- IP CONFIGURATION (stays on bottom always) ---
    ttk.Label(footer, text="Network IP:").pack(side=tk.LEFT, padx=6, pady=6)

    ip_entry = ttk.Entry(footer, width=20)
    ip_entry.pack(side=tk.LEFT, padx=6, pady=6)
    ip_entry.insert(0, "127.0.0.1")

    def on_set_ip_click():
        controller.netSetIp(ip_entry.get().strip())

    ttk.Button(footer, text="Set Network IP", command=on_set_ip_click).pack(side=tk.LEFT, padx=6, pady=6)

    # keybinds 
    current_screen = {"screen": None}

    def show_screen(new_screen):
        if current_screen["screen"] is not None:
            current_screen["screen"].destroy()
        current_screen["screen"] = new_screen
        new_screen.pack(in_=content, fill="both", expand=True)
    
    def f12Clear(event):
        if current_screen["screen"] is not None and hasattr(current_screen["screen"], "on_f12"):
            current_screen["screen"].on_f12()
        else:
            controller.clearItAll()

    def f5Start(event):
        if current_screen["screen"] is not None and hasattr(current_screen["screen"], "on_f5"):
            current_screen["screen"].on_f5()

    def f1Entry(event):
        if current_screen["screen"] is not None and hasattr(current_screen["screen"], "on_f1"):
            current_screen["screen"].on_f1()

    def f3Start(event):
        # Placeholder: same behavior as F5 for now
        if current_screen["screen"] is not None and hasattr(current_screen["screen"], "on_f5"):
            current_screen["screen"].on_f5()

    root.bind("<F1>", f1Entry)
    root.bind("<F3>", f3Start)
    root.bind("<F12>", f12Clear)
    root.bind("<F5>", f5Start)

    # Splash screen 
    splash_frame = tk.Frame(content, bg="black")
    splash_frame.pack(fill="both", expand=True)

    splash_label = tk.Label(
        splash_frame,
        text="",
        fg="white",
        bg="black",
        font=("Times New Roman", 28, "bold")
    )
    splash_label.pack(expand=True)

    # Try to load Jim's logo from assets/logo.jpg.
    # If it fails (missing file or jpg unsupported), fall back to text.
    assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
    logo_path = os.path.join(assets_dir, "logo.png")
    logo_path = os.path.normpath(logo_path)

    logo_img = None
    try:
        logo_img = tk.PhotoImage(file=logo_path)

        scale = 5
        logo_img = logo_img.subsample(scale, scale)

        splash_label.configure(image=logo_img, text="")
        splash_label.image = logo_img  # keep reference
    except Exception:
        splash_label.configure(text="Splash Time!")

    # Emma make sure to show Jim's logo from assets/logo.jpg
    # After 3 seconds, the player should go to Entry/Beginning screen 
    def goToBegin():
        splash_frame.destroy()

        # This is just a placeholder right now so that the repo can run.
        # Hey Emma, make sure to replace this with the real Entry screen UI.
        def goToAction():
            def backToEntry():
                entry = EntryScreen(content, on_start_game=goToAction)
                show_screen(entry)
            show_screen(ActionScreen(content, on_return_entry=backToEntry))

        entry = EntryScreen(content, on_start_game=goToAction)
        show_screen(entry)

    root.after(MS_SplashTime, goToBegin)

    controller.netBeginUDP_Listener()

    root.mainloop()
