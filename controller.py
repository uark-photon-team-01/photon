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
    return {
        "phase": state.phase,
        "time_remaining": state.time_remaining,
        "red_total_score": getRedTotalScore(),
        "green_total_score": getGreenTotalScore(),
        "event_log": list(state.eventLog),
        "red_roster": getSortedRedRoster(),
        "green_roster": getSortedGreenRoster(),
    }

def sortRosterKey(player):
    """
    Score is sorted from highest to lowest.
    If there's a tie, the codenames are sorted alphabetically
    """
    return (-player.score, player.codename.lower())


def getSortedRedRoster():
    """
    The red roster sorted by score from highest to lowest and returned
    If there's a tie, the codenames are sorted alphabetically
    """
    return sorted(state.redTeam, key=sortRosterKey)


def getSortedGreenRoster():
    """
    The green roster sorted by score from highest to lowest and returned
    If there's a tie, the codenames are sorted alphabetically
    """
    return sorted(state.greenTeam, key=sortRosterKey)

def changePhase(phase):
    """
    This function changes what part of the app we are in.
    Using this, the UI can pick which screen will be shown.
    """
    state.phase = phase
    recordLog("The current phase of the Game is " + str(phase) + ".")

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

def findPlayerByEquipmentID(equipmentID):
    """
    A player in can be found in either roster using their equipment/transmitter ID.
    The PlayerData object is returned or None if not found.
    """
    for player in state.redTeam + state.greenTeam:
        if player.equipmentID == equipmentID:
            return player
    return None


def playersAreOnSameTeam(playerOne, playerTwo):
    """
    If both players are on the same team this will return true.
    """
    if playerOne is None or playerTwo is None:
        return False
    return playerOne.team == playerTwo.team

def applyNormalHitScore(tagger, tagged):
    """
    The normal pvp scoring rules are applied

    Ex: if an opponent is hit:
        tagger +10

    if someone is hit on the same-team:
        tagger -10
        tagged -10
    """
    if playersAreOnSameTeam(tagger, tagged):
        tagger.score -= 10
        tagged.score -= 10
        recordLog(
            f"Uh Oh! There was a same team hit! Player {tagger.codename} hit teammate {tagged.codename}. "
            f"Sadly, both players now lose 10 points."
        )
    else:
        tagger.score += 10
        recordLog(
            f"Great! A hit was scored. Player {tagger.codename} tagged {tagged.codename}. "
            f"{tagger.codename} gains 10 points."
        )

def applyBaseHitScore(tagger, baseCode):
    """
    Base scoring will be based on the hit code.
    Players who trigger the base event are marked with a base icon.
    """
    
    if baseCode == 53:
        tagger.score += 100
        tagger.has_baseIcon = True
        recordLog(
            f"The was a score on a base. Player {tagger.codename} triggered base code 53. "
            f"Green wins 100 points."
        )

    elif baseCode == 43:
        tagger.score += 100
        tagger.has_baseIcon = True
        recordLog(
            f"The was a score on a base. Player {tagger.codename} triggered base code 43. "
            f"Red wins 100 points."
        )

def applyEvent(event):
    """

    When applying incoming events, the game logic function is used.

    """
    if state.phase != "PLAYING":
        recordLog("The event was ignored because the game is not in the Playing phase at the moment.")
        return False

    eventType = str(event.get("type", "")).upper()

    transmitterID = event.get("transmitter")
    hitID = event.get("hit")

    if transmitterID is None or hitID is None:
        recordLog(f"An Invalid event was received. There's a missing transmitter or hit field -> {event}")
        return False

    tagger = findPlayerByEquipmentID(transmitterID)
    if tagger is None:
        recordLog(f"An Invalid event was received. There was no player found with equipment ID {transmitterID}.")
        return False

    if eventType == "BASE":
        if hitID not in (43, 53):
            recordLog(f"An Invalid base event was received. There was a unsupported base code {hitID}.")
            return False

        applyBaseHitScore(tagger, hitID)
        return True

    if eventType == "TAG":
        tagged = findPlayerByEquipmentID(hitID)

        if tagged is None:
            recordLog(f"An Invalid tag event was received.  There's no player found with the equipment ID {hitID}.")
            return False

        if tagger.equipmentID == tagged.equipmentID:
            recordLog(f"An Invalid tag event was received. The Player {tagger.codename} cannot tag themselves.")
            return False

        applyNormalHitScore(tagger, tagged)
        return True

    recordLog(f"An Invalid event was received. There was an unknown event type '{eventType}'.")
    return False

def buildEventFromTransmitHit(transmitterID, hitID):
    """
    The raw transmitter:hit values are converted into the event shapes used by applyEvent().
    Caleb's receiver can call this later.
    """
    if hitID in (43, 53):
        return {
            "type": "BASE",
            "transmitter": transmitterID,
            "hit": hitID
        }

    return {
        "type": "TAG",
        "transmitter": transmitterID,
        "hit": hitID
    }

def isBaseCode(hitID):
    """
    if the hit ID is one of the project base codes then this should return true
    """
    return hitID in (43, 53)

def parseUDPMessage(rawMessage):
    """
    Here, raw UDP strings are converted into a parsed event dictionary.
    if the input is valid, a dictionary is returned.
    if the input is invalid, nothing is returned
    """
    if rawMessage is None:
        recordLog("There was an invalid UDP input error: the message was None.")
        return None

    text = str(rawMessage).strip()

    if text == "":
        recordLog("There was an invalid UDP input error: the message is empty.")
        return None

    if ":" not in text:
        recordLog(f"There was an invalid UDP input error: there is a missing ':' separator in the following: {text}")
        return None

    parts = text.split(":")

    if len(parts) != 2:
        recordLog(f"There was an invalid UDP input error: There was an expected transmitter and hit format in {text}")
        return None

    transmitterText = parts[0].strip()
    hitText = parts[1].strip()

    if transmitterText == "" or hitText == "":
        recordLog(f"There was an invalid UDP input error: there is a missing transmitter or hit value in {text}")
        return None

    try:
        transmitterID = int(transmitterText)
        hitID = int(hitText)
    except ValueError:
        recordLog(f"There was an invalid UDP input error: the transmitter and hit has to be integers in {text}")
        return None

    if isBaseCode(hitID):
        return {
            "type": "BASE",
            "transmitter": transmitterID,
            "hit": hitID
        }

    return {
        "type": "TAG",
        "transmitter": transmitterID,
        "hit": hitID
    }

def validateEvent(event):
    """
    Before applyEvent() changes any scores, a parsed event is validated
    if valid this function returns true. if false, it returns false.
    """
    if event is None:
        return False

    if state.phase != "PLAYING":
        recordLog("The event was ignored because the game is not in the Playing phase at the moment.")
        return False

    eventType = str(event.get("type", "")).upper()
    transmitterID = event.get("transmitter")
    hitID = event.get("hit")

    if eventType not in ("TAG", "BASE"):
        recordLog(f"Invalid event error: there is an unknown type in {event}")
        return False

    if transmitterID is None or hitID is None:
        recordLog(f"Invalid event error: there is a missing transmitter or hit in {event}")
        return False

    tagger = findPlayerByEquipmentID(transmitterID)
    if tagger is None:
        recordLog(f"Invalid event error: the transmitter equipment ID {transmitterID} is unknown.")
        return False

    if eventType == "BASE":
        if not isBaseCode(hitID):
            recordLog(f"Invalid base event error: the following base code is not supported {hitID}.")
            return False
        return True

    tagged = findPlayerByEquipmentID(hitID)
    if tagged is None:
        recordLog(f"Invalid tag event error: there was no player found with the following equipment ID: {hitID}.")
        return False

    if transmitterID == hitID:
        recordLog(f"Invalid tag event error: the player {transmitterID} cannot tag themselves.")
        return False

    return True

def handleIncomingUDPMessage(rawMessage):
    """
    """
    parsedEvent = parseUDPMessage(rawMessage)

    if not validateEvent(parsedEvent):
        return False

    return applyEvent(parsedEvent)

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

    udp.netBeginUDP_Listener(handleIncomingUDPMessage)
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
