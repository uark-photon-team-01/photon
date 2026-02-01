"""
What is the purpose of this file?
- ALL PostgreSQL code lives here.
- Do not let she UI talk to Postgres directly.
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
from psycopg2 import sql # this is used for advanced SQL building later


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
    """Here, you open a new database connection.

    The structure should be simple: open -> do one operation -> close.

    Will, If you get an auth error, try:
    - uncommenting password/host/port above, it should work then
    """
    return psycopg2.connect(**connection_params)


# -----------------------------------------------------------------------------------
# Main database functions (The controller will call these!)
# ------------------------------------------------------------------------------------

def obtainCodename(playerID):
    """Here write code to look up a player's codename by playerID.

    If a codename is found it should returned as a string.
    If a codename is not found, then the return should be None


    Hey Will, you should see the exact column names on the VM.
    Jim's python-pg.py uses: players (id, codename)
    so let's assume the columns are (id, codename).

    Quick check to confirm the columns on VM (run in terminal):
      psql -d photon
      \d players #this prints the player table columns
    """

    conn = dbconnect()
    try:
        curse = conn.cursor()

        # If this fails, the column might be player_id instead of id.
        curse.execute("SELECT codename FROM players WHERE id = %s;", (playerID,))
        row = curse.fetchone()

        if row is None:
            return None

        return row[0]
    finally:
        conn.close()


def addPlayer(playerID, codename):
    """Here, insert a new player into the DB.

    Will you need to:
    - Make sure the columns match (id, codename)
    - Figure out what to do if a playerID already exists:
        You could raise the error (fine) or update the codename.
        Do not alter the schema. Inserts should be fine tho.

    """

    conn = dbconnect()
    try:
        curse = conn.cursor()

        # This is the Insert pattern Jim used
        curse.execute(
            "INSERT INTO players (id, codename) VALUES (%s, %s);",
            (playerID, codename),
        )

        conn.commit()
    finally:
        conn.close()


# -----------------------------------------------------------------------------
# Controller-friendly wrappers (this matches the INTERNALS.md function names)
# -----------------------------------------------------------------------------
# These wrappers let the controller keep the stub names from Internals.md.
# this make it easy to change names in the future


def dbGetCodename(playerID):
    """Wrapper for the controller stub name.
      Should return (foundBool, codenameOrNone)
    """
    name = obtainCodename(playerID)
    if name is None:
        return (False, None)
    return (True, name)


def dbInsertPlayer(playerID, codename):
    """Wrapper for the controller stub name.
    Should return True if insert worked, False if it failed.
    """
    try:
        addPlayer(playerID, codename)
        return True
    except Exception as e:
        print("Oh Nooo! There was a database insert error. It is:", e)
        return False


# -----------------------------------------------------------------
# Week 1 proof / quick testing (based on Jim's starter code)
# -----------------------------------------------------------------

def testOurConnection():
    """Here, you prove that PostgreSQL connects.
    Our boy Jimmy used the SELECT version(); so we are gonna do the same.
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
        print("Oh Nooo! There was a database insert error. It is:", e)
        return False


def listOfPlayers(limit=10):
    """ For Week 1, just print some rows for debugging purposes."""

    conn = dbconnect()
    try:
        curse = conn.cursor()
        curse.execute("SELECT id, codename FROM players ORDER BY id LIMIT %s;", (limit,))
        rows = curse.fetchall()
        for row in rows:
            print(row)
    finally:
        conn.close()


# -----------------------------------------------------------------
# Sprint 2 / Week 2 integration notes (Bro read this)
# -----------------------------------------------------------------
# Info about the integration:
# - The controller flow should be:
#     nameFound = obtainCodename(playerID)
#     if Foundname is None:
#         UI asks the user for the codename
#         addPlayer(playerID, codename)
#         nameFound = codename
# - Afterwards the controller would continue with the equipmentID & UDP broadcast.
# Keep in mind that this pice of code should never call tkinter or UDP.


if __name__ == "__main__":
    # Here is the Week 1 test:
    # Make sure that this file is run from the repo root 
    # Use the following command in the terminal: python3 db/database.py
    if testOurConnection():
        print("Here's an example list of players:")
        listOfPlayers(5)

        # Hey Will, try a lookup on an existing id
        # print(obtainCodename(1))

        # Also, try inserting a test user (then check to see if it appears)
        # addPlayer(500, "BhodiLi")  # Here's an example Jim used.
