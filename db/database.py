"""
What is the purpose of this file?
- ALL PostgreSQL code lives here.
- Do not let the UI talk to Postgres directly.
- The controller should call functions in this file.

Sprint 2 / Week 1-2 goals for this file:
- Week 1: prove we can connect/lookup codenames & insert a new player.
- Week 2: Player Entry screen flow:
    1) User enters playerID
    2) App looks up the codename in the database
    3) If missing, the user types a codename and the app inserts it

Constraints from Jim:
- The database is already installed on the Debian VM.
- Database name: photon
- Table: players
- Do NOT alter schema (that means no CREATE/ALTER/DROP). Only SELECT/INSERT/DELETE rows.

---
The parts of code that were pulled from Jim's repo were:
- Connection style + parameters 
- Insert example
- Jim also includes a file named player.sql, we do not need that!
- So don't run it (AND do not create/alter tables).
"""

# This code is from Jim's repo: python-pg.py
import psycopg2
from psycopg2 import sql  # this is used for advanced SQL building later


# -----------------------------------------------------------------
# This is the connection settings 
# -----------------------------------------------------------------
# For some Debian VMs, password/host/port are not needed for a local database.
connection_params = {
    "dbname": "photon",
    "user": "student",
    # "password": "student",  # Hey Will, uncomment this if the Virtual Machine needs it 
    # "host": "localhost",
    # "port": "5432",
}


def dbconnect():
    """Open a new database connection.

    The structure should be simple: open -> do one operation -> close.

    Will, If you get an auth error, try:
    - uncommenting password/host/port above, it should work then
    
    Returns:
        psycopg2.connection: Active database connection
    """
    return psycopg2.connect(**connection_params)


# -----------------------------------------------------------------------------------
# Main database functions (The controller will call these!)
# ------------------------------------------------------------------------------------

def obtainCodename(playerID):
    """Look up a player's codename by playerID.

    If a codename is found it should be returned as a string.
    If a codename is not found, then the return should be None

    Args:
        playerID (int): The player's ID number

    Returns:
        str: The player's codename if found
        None: If no player with that ID exists

    Note: 
        Column names are (id, codename) based on Jim's schema.
        If this fails, the column might be player_id instead of id.
        To verify run: psql -d photon, then \d players
    """

    conn = dbconnect()
    try:
        curse = conn.cursor()

        # Query for the codename matching this player ID
        # Using parameterized query to prevent SQL injection
        curse.execute("SELECT codename FROM players WHERE id = %s;", (playerID,))
        row = curse.fetchone()

        # If no row found, player doesn't exist
        if row is None:
            return None

        # Return the codename (first column of the result)
        return row[0]
    finally:
        conn.close()


def addPlayer(playerID, codename):
    """Insert a new player into the database.

    This will insert a new row with the given playerID and codename.
    
    Important: If a playerID already exists, this will raise an exception
    because of the primary key constraint. This is intentional - it prevents
    accidentally overwriting existing players.

    Args:
        playerID (int): The player's ID number
        codename (str): The player's chosen codename

    Raises:
        psycopg2.IntegrityError: If playerID already exists (duplicate primary key)
        psycopg2.Error: For other database errors

    Note:
        Do not alter the schema. This only does INSERTs.
        Columns must match: (id, codename)
    """

    conn = dbconnect()
    try:
        curse = conn.cursor()

        # Insert the new player using parameterized query
        # This is the Insert pattern Jim used
        curse.execute(
            "INSERT INTO players (id, codename) VALUES (%s, %s);",
            (playerID, codename),
        )

        # Commit the transaction to save changes
        conn.commit()
    finally:
        conn.close()


def updatePlayer(playerID, newCodename):
    """Update an existing player's codename.

    This will update the codename for a player that already exists in the database.
    
    Args:
        playerID (int): The player's ID number
        newCodename (str): The new codename to set

    Returns:
        bool: True if a row was updated, False if player doesn't exist

    Raises:
        psycopg2.Error: For database errors
    """

    conn = dbconnect()
    try:
        curse = conn.cursor()

        # Update the player's codename
        curse.execute(
            "UPDATE players SET codename = %s WHERE id = %s;",
            (newCodename, playerID),
        )

        # Check how many rows were affected
        rows_updated = curse.rowcount

        # Commit the transaction
        conn.commit()

        # Return True if at least one row was updated
        return rows_updated > 0
    finally:
        conn.close()


# -----------------------------------------------------------------------------
# Controller-friendly wrappers (this matches the INTERNALS.md function names)
# -----------------------------------------------------------------------------
# These wrappers let the controller keep the stub names from Internals.md.
# This makes it easy to change names in the future


def dbGetCodename(playerID):
    """Wrapper for the controller stub name.
    
    This provides a clean interface for the controller to check if a player exists
    and get their codename in one call.
    
    Args:
        playerID (int): The player's ID to look up
    
    Returns:
        tuple: (status, codenameOrNone)
            - ("found", "PlayerName") if player exists
            - ("not_found", None) if player doesn't exist in DB
            - ("db_error", None) if database error occurred
    """
    try:
        name = obtainCodename(playerID)
        if name is None:
            return ("not_found", None)
        return ("found", name)
    except Exception as e:
        print(f"Database error in dbGetCodename: {e}")
        return ("db_error", None)


def dbInsertPlayer(playerID, codename):
    """Wrapper for the controller stub name.
    
    This provides a clean interface for the controller to add new players
    with clear success/failure indication.
    
    Args:
        playerID (int): The player's ID number
        codename (str): The player's chosen codename
    
    Returns:
        str: Status of the operation
            - "success" if insert worked
            - "duplicate" if player ID already exists
            - "db_error" if other database error occurred
    """
    try:
        addPlayer(playerID, codename)
        return "success"
    except Exception as e:
        error_msg = str(e).lower()
        # Check if it's a duplicate key error
        if "duplicate" in error_msg or "unique" in error_msg or "already exists" in error_msg:
            print(f"Player {playerID} already exists in database")
            return "duplicate"
        else:
            print(f"Database error in dbInsertPlayer: {e}")
            return "db_error"


def dbUpdatePlayer(playerID, newCodename):
    """Update an existing player's codename.
    
    This provides a clean interface for the controller to update player codenames.
    
    Args:
        playerID (int): The player's ID number
        newCodename (str): The new codename to set
    
    Returns:
        str: Status of the operation
            - "success" if update worked
            - "not_found" if player doesn't exist
            - "db_error" if database error occurred
    """
    try:
        was_updated = updatePlayer(playerID, newCodename)
        if was_updated:
            return "success"
        else:
            return "not_found"
    except Exception as e:
        print(f"Database error in dbUpdatePlayer: {e}")
        return "db_error"


# -----------------------------------------------------------------
# Week 1 proof / quick testing (based on Jim's starter code)
# -----------------------------------------------------------------

def testOurConnection():
    """Prove that PostgreSQL connects.
    
    Our boy Jimmy used the SELECT version(); so we are gonna do the same.
    This is a simple test to make sure the database is reachable and responding.
    
    Returns:
        bool: True if connection successful, False otherwise
    """

    try:
        conn = dbconnect()
        curse = conn.cursor()

        # Get the PostgreSQL version to prove we're connected
        curse.execute("SELECT version();")
        version = curse.fetchone()[0]
        print("Connected to -", version)

        conn.close()
        return True
    except Exception as e:
        print("Oh Nooo! There was a database connection error. It is:", e)
        return False


def listOfPlayers(limit=10):
    """For Week 1, just print some rows for debugging purposes.
    
    This is a helper function to see what's in the database during development.
    
    Args:
        limit (int): Maximum number of players to display (default: 10)
    """

    conn = dbconnect()
    try:
        curse = conn.cursor()
        
        # Get the first N players ordered by ID
        curse.execute("SELECT id, codename FROM players ORDER BY id LIMIT %s;", (limit,))
        rows = curse.fetchall()
        
        # Print each player
        print(f"\n=== Players in Database (showing up to {limit}) ===")
        for row in rows:
            print(f"  ID: {row[0]:>5} | Codename: {row[1]}")
        print("=" * 45)
    finally:
        conn.close()


# -----------------------------------------------------------------
# Sprint 2 / Week 2 integration notes (Bro read this)
# -----------------------------------------------------------------
# Info about the integration:
# - The controller flow should be:
#     found, codename = dbGetCodename(playerID)
#     if not found:
#         # UI asks the user for the codename
#         success = dbInsertPlayer(playerID, codename)
#         if success:
#             # Continue with the game
#         else:
#             # Handle error (maybe ID already exists?)
#     else:
#         # Player exists, use the codename we found
# 
# - Afterwards the controller would continue with the equipmentID & UDP broadcast.
# Keep in mind that this piece of code should never call tkinter or UDP.
# That stuff lives in the controller and UI layers.


if __name__ == "__main__":
    # Here is the Week 1 test:
    # Make sure that this file is run from the repo root 
    # Use the following command in the terminal: python3 db/database.py
    
    print("\n" + "=" * 60)
    print("WEEK 1 DATABASE CONNECTION TEST")
    print("=" * 60)
    
    if testOurConnection():
        print("\n✓ Database connection successful!\n")
        
        print("Here's an example list of players:")
        listOfPlayers(5)

        # Hey Will, try a lookup on an existing id
        print("\n--- Testing obtainCodename() ---")
        print("Looking up player ID 1...")
        result = obtainCodename(1)
        if result:
            print(f"  Found: {result}")
        else:
            print("  Not found (player doesn't exist)")

        # Also, try inserting a test user (then check to see if it appears)
        print("\n--- Testing addPlayer() ---")
        print("Note: Uncomment the line below to test inserting a player")
        # addPlayer(500, "BhodiLi")  # Here's an example Jim used.
        # print("  Inserted player 500: BhodiLi")
        # print("\nUpdated player list:")
        # listOfPlayers(5)
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60 + "\n")
    else:
        print("\n✗ Database connection failed!")
        print("Check your connection_params and make sure PostgreSQL is running.\n")
