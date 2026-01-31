# IMPORTANT INFO:
# - Emma your UI Code should call these controller functions.
# - Also, your UI code shouldn't directly talk to Will's database or Caleb's UDP network code.
# - This is because the controller keeps everything consistent and prevents confusion.

from model import GameState, PlayerData

# This is the app's only shared game state.
# Everyone will read & write through this object.
state = GameState()


# ------------------------------
# Basic Functions You Will Need
# ------------------------------

def grabState():
    """
    The UI will call this to read the current state of the game.
    For Example: reveal the roster, show timer, and text from the log.
    """
    return state


def changePhase(phase):
    """
    This will change what part of the app we are in.
    For Example: "Splash", "Beginning", "Playing", etc.
    The UI can use this to decide which screen will be shown.
    """
    state.phase = phase
    recordLog("The Game is now in the " + str(phase), " phase.")


def recordLog(message):
    """
    Use this to add messages to the event log.
    These messages will displayed to the action screen later. 
    """
    state.eventLog.append(str(message))


def clearItAll():
    """
    This will clear everything and reset the game back to the beginning phase.
    The button/key to do this needs to be (F12).
    """
    state.redTeam.clear()
    state.greenTeam.clear()
    state.eventLog.clear()

    state.time_remaining = 0
    state.phase = "Beginning"

    recordLog("All players have been cleared and the game has been reset.")


def addPlayerToTeam(team, playerID, codename, equipmentID):
    """
    When the user enters a player to a roster this is called.
    This will strore the player in the correct roster (red/green).
    Later, this will also trigger the UDP broadcast of equipmentID.
    """

    capitalTeamname = str(team).upper() #Converts the team names to Uppercase so inputs can be compared easily

    # With the new inputed info, a new PlayerData object is created. 
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
    # Since this is Week 1, there is no real UDP yet, so we call a "Net Stub".
    networkBC_eqmt(equipmentID)
