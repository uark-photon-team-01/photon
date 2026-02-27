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

Database behavior rules:
- If a player ID is already in the database, use that codename as-is. Do NOT update it.
- If a player ID is not in the database, allow a new insert.
- No UPDATE, no CREATE, no ALTER, no TRUNCATE. Only SELECT, INSERT, and targeted DELETE.

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
# Connection settings
# -----------------------------------------------------------------
# For some Debian VMs, password/host/port are not needed for a local database.
connection_params = {
    "dbname": "photon",
    # "user": "student",
    # "password": "student",  # Hey Will, uncomment this if the Virtual Machine needs it
    # "host": "localhost",
    # "port": "5432",
}


def dbconnect():
    """Open a new database connection.

    The structure should be simple: open -> do one operation -> close.

    Will, if you get an auth error, try:
    - uncommenting password/host/port above, it should work then

    Returns:
        psycopg2.connection: Active database connection
    """
    return psycopg2.connect(**connection_params)


# -----------------------------------------------------------------------------------
# Main database functions (The controller will call these!)
# -----------------------------------------------------------------------------------

def obtainCodename(playerID):
    """Look up a player's codename by playerID.

    Args:
        playerID (int): The player's ID number

    Returns:
        str: The player's codename if found
        None: If no player with that ID exists

    Note:
        Column names are (id, codename) based on Jim's schema.
        If this fails, the column might be player_id instead of id.
        To verify run: psql -d photon, then \\d players
    """
    conn = dbconnect()
    try:
        curse = conn.cursor()
        curse.execute("SELECT codename FROM players WHERE id = %s;", (playerID,))
        row = curse.fetchone()
        if row is None:
            return None
        return row[0]
    finally:
        conn.close()


def addPlayer(playerID, codename):
    """Insert a new player into the database.

    Only call this after confirming the player does NOT already exist.
    If a playerID already exists, this will raise an IntegrityError because
    of the primary key constraint — that is intentional.

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
        curse.execute(
            "INSERT INTO players (id, codename) VALUES (%s, %s);",
            (playerID, codename),
        )
        conn.commit()
    finally:
        conn.close()


def deletePlayer(playerID):
    """Delete a specific player from the database.

    Only use this for removing test players when needed.
    Do not call this during normal gameplay.

    Args:
        playerID (int): The player's ID number to delete

    Returns:
        bool: True if a row was deleted, False if player didn't exist
    """
    conn = dbconnect()
    try:
        curse = conn.cursor()
        curse.execute("DELETE FROM players WHERE id = %s;", (playerID,))
        rows_deleted = curse.rowcount
        conn.commit()
        return rows_deleted > 0
    finally:
        conn.close()


# -----------------------------------------------------------------------------
# Controller-friendly wrappers
# -----------------------------------------------------------------------------
# These wrappers let the controller keep the stub names from Internals.md.
# All functions return a clear status string every time — no booleans, no bare None.
#
# Controller flow:
#     status, codename = dbGetCodename(playerID)
#     if status == "found":
#         # Player exists — use codename as-is, do NOT update it
#     elif status == "not_found":
#         # UI asks user for a codename, then call dbInsertPlayer()
#         insert_status = dbInsertPlayer(playerID, codename)
#         if insert_status == "success":
#             # Continue with the game
#         elif insert_status == "duplicate":
#             # Rare race condition — player was inserted between the lookup and insert
#         else:
#             # "db_error" — handle the failure
#     else:
#         # "db_error" — handle the failure


def dbGetCodename(playerID):
    """Look up a player's codename by ID.

    If the player is found, the codename is returned as-is. The controller
    must NOT attempt to update the database row in that case.

    Args:
        playerID (int): The player's ID to look up

    Returns:
        tuple: (status, codename_or_none)
            - ("found",     "PlayerName") if player exists
            - ("not_found", None)         if player is not in the DB
            - ("db_error",  None)         if a database error occurred
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
    """Insert a new player into the database.

    Only call this when dbGetCodename returned "not_found".
    Never call this to overwrite or refresh an existing player.

    Args:
        playerID (int): The player's ID number
        codename (str): The player's chosen codename

    Returns:
        str: Status of the operation
            - "success"   if the insert worked
            - "duplicate" if the player ID already exists
            - "db_error"  if another database error occurred
    """
    try:
        # Explicitly check for existing player first to guarantee duplicate
        # detection regardless of how psycopg2/PostgreSQL handles IntegrityError
        existing = obtainCodename(playerID)
        if existing is not None:
            print(f"Player {playerID} already exists in database")
            return "duplicate"
        addPlayer(playerID, codename)
        return "success"
    except Exception as e:
        error_msg = str(e).lower()
        if "duplicate" in error_msg or "unique" in error_msg or "already exists" in error_msg:
            print(f"Player {playerID} already exists in database")
            return "duplicate"
        else:
            print(f"Database error in dbInsertPlayer: {e}")
            return "db_error"


def dbDeletePlayer(playerID):
    """Delete a specific player — for test cleanup only.

    Do not use this during normal gameplay.

    Args:
        playerID (int): The player's ID number to remove

    Returns:
        str: Status of the operation
            - "success"   if the player was deleted
            - "not_found" if no player with that ID existed
            - "db_error"  if a database error occurred
    """
    try:
        was_deleted = deletePlayer(playerID)
        if was_deleted:
            return "success"
        else:
            return "not_found"
    except Exception as e:
        print(f"Database error in dbDeletePlayer: {e}")
        return "db_error"


# -----------------------------------------------------------------
# Week 1 proof / quick testing
# -----------------------------------------------------------------

def testOurConnection():
    """Prove that PostgreSQL connects.

    Our boy Jimmy used SELECT version(); so we are gonna do the same.

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        conn = dbconnect()
        curse = conn.cursor()
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

    Args:
        limit (int): Maximum number of players to display (default: 10)
    """
    conn = dbconnect()
    try:
        curse = conn.cursor()
        curse.execute("SELECT id, codename FROM players ORDER BY id LIMIT %s;", (limit,))
        rows = curse.fetchall()
        print(f"\n=== Players in Database (showing up to {limit}) ===")
        for row in rows:
            print(f"  ID: {row[0]:>5} | Codename: {row[1]}")
        print("=" * 45)
    finally:
        conn.close()


if __name__ == "__main__":
    # Week 1 test:
    # Make sure this file is run from the repo root
    # Command: python3 db/database.py

    print("\n" + "=" * 60)
    print("Simple Database Connection Test")
    print("=" * 60)

    if testOurConnection():
        print("\n Database connection successful!\n")

        print("Here's an example list of players:")
        listOfPlayers(5)

        # Test a lookup on an existing ID
        print("\n--- Testing dbGetCodename() ---")
        print("Looking up player ID 1...")
        status, codename = dbGetCodename(1)
        if status == "found":
            print(f"  Found: {codename}")
        elif status == "not_found":
            print("  Not found (player doesn't exist)")
        else:
            print("  Database error during lookup")

        # Test an insert (uncomment to run)
        print("\n--- Testing dbInsertPlayer() ---")
        print("Note: Uncomment the lines below to test inserting a player")
        # result = dbInsertPlayer(500, "BhodiLi")
        # print(f"  Insert result: {result}")
        # if result == "success":
        #     print("  Player inserted successfully")
        #     print("\nUpdated player list:")
        #     listOfPlayers(5)

        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60 + "\n")
    else:
        print("\n Database connection failed!")
        print("Check your connection_params and make sure PostgreSQL is running.\n")
