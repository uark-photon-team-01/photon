# IMPORTANT INFO:
# - Emma your UI Code should call these controller functions.
# - Also, your UI code shouldn't directly talk to Will's database or Caleb's UDP network code.
# - This is because the controller keeps everything consistent and prevents confusion.

from model import Game_State, PlayerData
from net import udp  # Caleb added
from db import database  # Will's database functions - REAL DB CONNECTION!
import time

# This is the app's only shared game state.
# Everyone will read & write through this object.
state = Game_State()
warningSeconds = 30
playSeconds = 6 * 60

lastTickOfTimer = None


# ------------------------------
# Basic Functions You Will Need
# ------------------------------

def grabState():
    """
    The UI will call this to read the current state of the game.
    For Example: reveal the roster, show timer, and text from the log.
    """
    return state

def getRedTotalScore():
    return sum(player.score for player in state.redTeam)


def getGreenTotalScore():
    return sum(player.score for player in state.greenTeam)


def getActionSnapshot():
    """
    One clean payload for Emma's Action screen.
    """
    return {
        "phase": state.phase,
        "time_remaining": state.time_remaining,
        "red_total_score": getRedTotalScore(),
        "green_total_score": getGreenTotalScore(),
        "event_log": list(state.eventLog),
        "red_roster": list(state.redTeam),
        "green_roster": list(state.greenTeam),
    }


def changePhase(phase):
    """
    This will change what part of the app we are in.
    For Example: "Splash", "Beginning", "Playing", etc.
    The UI can use this to decide which screen will be shown.
    """
    state.phase = phase
    recordLog("The Game is now in the " + str(phase) + " phase.")


def recordLog(message):
    """
    Use this to add messages to the event log.
    These messages will displayed to the action screen later.
    """
    state.eventLog.append(str(message))

def resetTheActionState():
    """
    For new matches, reset the gameplay state.

    This won't remove players from the rosters.
    It only resets things that live in the live action screen / match state.
    """
    global lastTickOfTimer

    for player in state.redTeam + state.greenTeam:
        player.score = 0
        player.has_baseIcon = False

    state.eventLog.clear()
    state.time_remaining = 0
    state.timer_running = False
    lastTickOfTimer = None


def startGame():
    """
    Starts a new match.
    """
    global lastTickOfTimer

    resetTheActionState()

    state.phase = "WARNING"
    state.time_remaining = warningSeconds
    state.timer_running = True
    lastTickOfTimer = time.monotonic()

    recordLog("Game start has been requested.")
    recordLog("A 30-second warning countdown has begun. GET READY.")


def moveOneSecond():
    """
    This will advance the game clock by one second only.
    Phase transitions are handled here when the timer reaches zero.
    """
    if state.time_remaining > 0:
        state.time_remaining -= 1

    if state.time_remaining > 0:
        return

    if state.phase == "WARNING":
        state.phase = "PLAYING"
        state.time_remaining = playSeconds
        recordLog("The warning countdown is over. The live game has begun.")
        netBroadcastEquipment(202)

    elif state.phase == "PLAYING":
        state.phase = "ENDED"
        state.time_remaining = 0
        state.timer_running = False
        recordLog("Uh Oh! The Game clock has expired. Game ended.")

        for _ in range(3):
            netBroadcastEquipment(221)


def updateTimer():
    """
    This function will make sure that the controller clock is in sync with time.
    The user interface should call this on a short repeating sequence
    """
    global lastTickOfTimer

    if not state.timer_running:
        return state.time_remaining

    if lastTickOfTimer is None:
        lastTickOfTimer = time.monotonic()
        return state.time_remaining

    now = time.monotonic()
    secondsElapsed = int(now - lastTickOfTimer)

    if secondsElapsed <= 0:
        return state.time_remaining

    for _ in range(secondsElapsed):
        if not state.timer_running:
            break
        moveOneSecond()

    lastTickOfTimer += secondsElapsed
    return state.time_remaining


def formatTimeRemaining():
    """
    This is not used at the moment but will be for the Action screen later.
    """
    minutes, seconds = divmod(max(state.time_remaining, 0), 60)
    return f"{minutes}:{seconds:02d}"


def clearItAll():
    """
    This will clear everything and reset the game back to the beginning phase.
    The button/key to do this needs to be (F12).
    """
    state.redTeam.clear()
    state.greenTeam.clear()

    resetTheActionState()
    state.phase = "Beginning"

    recordLog("All players have been cleared and the game has been reset.")


def addPlayerToTeam(team, playerID, codename, equipmentID):
    """
    When the user enters a player to a roster this is called.
    This will store the player in the correct roster (red/green).
    Later, this will also trigger the UDP broadcast of equipmentID.
    """

    capitalTeamname = str(team).upper()  # Converts the team names to Uppercase so inputs can be compared easily

    # With the new inputted info, a new PlayerData object is created.
    player = PlayerData(
        playerID=playerID,
        codename=codename,
        equipmentID=equipmentID,
        team=capitalTeamname
    )

    # Put player into the correct team roster list
    if capitalTeamname == "RED":
        state.redTeam.append(player)
    elif capitalTeamname == "GREEN":
        state.greenTeam.append(player)
    else:
        # If the UI passes an incorrect team name, an error is stopped and a message shown
        raise ValueError("Uh Oh! Your team must be 'RED' or 'GREEN'.")

    # This is a play-by-play log line of what is happening
    recordLog("Added " + codename + " (ID: " + str(playerID) + ") to " +
              capitalTeamname + " with equipment " + str(equipmentID))

    # After a player is added, then equipmentID is broadcast
    netBroadcastEquipment(equipmentID)


# -------------------------------------------------
# REAL Database Functions (Not Stubs anymore!!!)
# -------------------------------------------------
# These now call Will's real database.py functions.
#
# Player lookup/insert flow:
#   1. Call dbGetCodename(playerID)
#   2. If "found"     → use the codename as-is. Do NOT insert or update.
#   3. If "not_found" → ask the user for a codename, then call dbInsertPlayer()
#   4. If "db_error"  → surface the error to the UI
#
# There is no update path. Existing players are always used as-is.

def dbGetCodename(playerID):
    """
    Looks up a player's codename in the database by playerID.

    Returns:
        tuple:
            - ("found",     "Codename") if player exists — use codename as-is
            - ("not_found", None)       if player is not in the DB
            - ("db_error",  None)       if a database error occurred
    """
    status, codename = database.dbGetCodename(playerID)
    return status, codename


def dbInsertPlayer(playerID, codename):
    """
    Inserts a new player into the database.

    Only call this after dbGetCodename returned "not_found".
    Never call this to overwrite an existing player.

    Returns:
        str:
            - "success"   if the insert worked
            - "duplicate" if the player ID already exists
            - "db_error"  if a database error occurred
    """
    status = database.dbInsertPlayer(playerID, codename)
    return status


# -------------------------------------------------
# Network Stubs (Caleb's code - these are working!)
# -------------------------------------------------

def netSetIp(ip):
    """
    Network Stub:
    Later on, Caleb is gonna store the IP and use it for UDP sockets.
    But for right now let's just log it.
    """
    udp.netSetIp(ip)
    recordLog("The network IP is set to " + str(ip))
    print("The network IP is set to " + str(ip))


def netBroadcastEquipment(equipmentID):
    """
    Network Stub:
    Here, Caleb will send the equipmentID out on UDP broadcast port 7500.
    For right now, let's just log what would be broadcast.
    """
    udp.netBroadcastEquipment(equipmentID)
    recordLog("This equipment ID " + str(equipmentID) + " would be broadcast.")


listener_is_running = False

def netBeginUDP_Listener():
    """
    Network Stub:
    Caleb will listen for hits after opening the UDP receive port 7501.
    For right now, let's log the fact that we start listening here.
    """
    global listener_is_running

    if listener_is_running == True:
        # If it's already running, do nothing!
        return

    udp.netBeginUDP_Listener(recordLog)
    recordLog("UDP Listener started on port 7501")

    listener_is_running = True


# -----------------------------
# Caleb Integration Test
# To Run type: python controller.py in one terminal. In another terminal, type :
# python -c "import socket; sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); sock.sendto(b'53', ('127.0.0.1', 7501)); print('Hit sent!')"
# -----------------------------
if __name__ == "__main__":
    import time

    print("--- 1. Testing System Reset ---")
    clearItAll()

    print("--- 2. Starting UDP Listener (Check for 'UDP received' messages) ---")
    netBeginUDP_Listener()

    print("--- 3. Testing Player Add & Broadcast ---")
    addPlayerToTeam("RED", 1, "Caleb", 112)

    print("--- SYSTEM IS LIVE ---")
    print("Waiting for hits on Port 7501...")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTest finished.")
        print("Final Event Log:", state.eventLog)
