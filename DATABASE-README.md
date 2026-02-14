# Photon Laser Tag System - Team One

## Team Members

| GitHub Username      | Real Name           |
|---------------------|---------------------|
| CentariB            | Centarrius Brooks   |
| WillBoone24         | Will Boone          |
| EmmaMah258          | Emma Mahaffey       |
| CollegeBoundCaleb   | Caleb Carpenter     |

---

## How to Run the Program

### Prerequisites
- Python 3.x installed
- PostgreSQL database installed and running
- Running on Debian/Ubuntu Linux (recommended) or compatible system

---

## Database Setup

### 1. **Verify PostgreSQL is installed and running**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# If not running, start it
sudo systemctl start postgresql
```

### 2. **Create the photon database**
```bash
# Switch to postgres user and create database
sudo -u postgres psql -c "CREATE DATABASE photon;"

# Verify database was created
psql -l | grep photon
```

### 3. **Create the players table**

The application requires a `players` table with the following schema:

```sql
# Connect to the photon database
psql -d photon

# Create the players table
CREATE TABLE players (
    id INTEGER PRIMARY KEY,
    codename TEXT NOT NULL
);

# Verify table was created
\d players

# Exit psql
\q
```

**Important Schema Details:**
- `id` (INTEGER, PRIMARY KEY): Unique player ID - **must be unique**, no duplicates allowed
- `codename` (TEXT, NOT NULL): Player's chosen codename/username

**Note:** The application does **NOT** modify the database schema. It only performs SELECT, INSERT, UPDATE, and DELETE operations on existing tables.

### 4. **Set up database permissions (if needed)**

If you encounter permission errors, ensure the `student` user has access:

```bash
# As postgres user, grant privileges
sudo -u postgres psql -d photon -c "GRANT ALL PRIVILEGES ON TABLE players TO student;"
```

### 5. **Test database connection**

You can test the database connection using our test script:

```bash
# Run the database test
python3 db/database.py
```

This should output:
- PostgreSQL version information
- List of existing players (if any)
- Confirmation that connection works

### 6. **Database configuration**

The application connects to PostgreSQL with these default settings (in `db/database.py`):

```python
connection_params = {
    "dbname": "photon",
    "user": "student",
    # "password": "student",  # Uncomment if your setup requires a password
    # "host": "localhost",
    # "port": "5432",
}
```

**If you need authentication:** Uncomment the `password`, `host`, and `port` lines in `db/database.py`.

### 7. **Verify everything works**

```bash
# Check that the table exists and is empty (or has test data)
psql -d photon -c "SELECT * FROM players;"

# Expected output: empty table or existing players
```

---

## Installation

1. **Run the install script:**
   ```bash
   bash install.sh
   ```
   This will install all required dependencies including:
   - Python3-tk (Tkinter for GUI)
   - psycopg2 (PostgreSQL adapter)
   - Other required Python packages

2. **If Tkinter fails to install automatically:**
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3-tk
   ```

### Running the Application

1. **Start the application:**
   ```bash
   python3 main.py
   ```

2. **What to expect:**
   - Splash screen appears for 3 seconds (displays logo)
   - Automatically transitions to Player Entry screen
   - Use the interface to add players to RED or GREEN teams
   - Players are automatically saved to PostgreSQL database
   - Equipment IDs are broadcast over UDP after each player addition

### Keyboard Shortcuts
- **F5** - Start the game (transition to action screen)
- **F12** - Clear all entries and reset the game

---

## Project Structure

```
.
├── main.py           # Application entry point - starts the whole app
├── install.sh        # Installation script for dependencies
├── controller.py     # Game logic controller (connects UI, DB, and network)
├── model.py          # Data models (Game_State, PlayerData)
├── db/
│   └── database.py   # PostgreSQL database interface
├── ui/
│   └── ui.py         # UI screens (Splash, Entry, Action)
├── net/
│   └── udp.py        # UDP socket networking (broadcast/receive)
└── assets/
    └── logo.png      # Splash screen logo and other media files
```

### File Descriptions

- **main.py** - Entry point that creates the main window and manages screen transitions (splash → entry → game)
- **install.sh** - Setup script that installs required software packages
- **controller.py** - Central controller managing game state and coordinating between UI, database, and network
- **model.py** - Defines data structures for game state and player information
- **db/database.py** - All PostgreSQL code for player lookup and insertion
- **ui/ui.py** - All screen/window code (how the app looks)
- **net/udp.py** - Network communication code for equipment broadcasts and hit detection
- **assets/** - Images and audio files used by the application

---

## Database Setup

The application expects a PostgreSQL database with the following configuration:

- **Database name:** `photon`
- **Username:** `student`
- **Table:** `players` with columns `(id, codename)`

**Note:** The application does **NOT** modify the database schema. It only performs SELECT, INSERT, UPDATE, and DELETE operations on existing tables.

---

## Network Configuration

The application uses UDP sockets for equipment communication:
- **Broadcast port:** 7500 (equipment ID broadcasts)
- **Receive port:** 7501 (hit detection)
- **Default IP:** 127.0.0.1 (can be changed via UI)

You can set a different network IP using the "Set Network IP" field at the bottom of the entry screen.

---

## Sprint 2 Deliverables

This sprint includes:
-  Git repository with team member real names
-  Splash screen (3-second logo display)
-  Player entry screen (add players to teams)
-  Database integration (PostgreSQL player storage)
-  UDP socket implementation (equipment broadcast)
-  Network selection option (configurable IP address)
-  Install script for dependencies
-  README with run instructions and team member table

---

## Troubleshooting

### Database Connection Issues
If you get database connection errors:
1. Verify PostgreSQL is running: `sudo systemctl status postgresql`
2. Check database exists: `psql -l | grep photon`
3. Verify table exists: `psql -d photon -c "\d players"`
4. If password required: Uncomment `password`, `host`, `port` lines in `db/database.py`

### Missing Players Table
If the `players` table doesn't exist, create it:
```bash
psql -d photon -c "CREATE TABLE players (id INTEGER PRIMARY KEY, codename TEXT NOT NULL);"
```

### Database Permission Errors
If you get permission denied errors:
```bash
# Grant privileges to student user
sudo -u postgres psql -d photon -c "GRANT ALL PRIVILEGES ON TABLE players TO student;"
```

### Duplicate Key Errors
If you try to add a player that already exists:
- The `id` column is a PRIMARY KEY and must be unique
- Use the "Update Codename" button to change existing player names
- Or choose a different player ID number

### Tkinter/GUI Issues
If the GUI doesn't appear:
1. Make sure you're running on a system with a display (not headless SSH)
2. Reinstall Tkinter: `sudo apt-get install --reinstall python3-tk`

### Network/UDP Issues
If equipment broadcasts aren't working:
1. Check firewall settings allow UDP ports 7500 and 7501
2. Verify the correct network IP is set in the application

---

## Development Notes

- All UI code should call controller functions (never access database or network directly)
- Database schema should NOT be modified by the application (read-only schema)
- UDP broadcasts happen automatically after each player is added to a team
