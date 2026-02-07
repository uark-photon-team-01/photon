# IMPORTANT INFO:
# - Emma your UI Code should call these controller functions.
# - Also, your UI code shouldn't directly talk to Will's database or Caleb's UDP network code.
# - This is because the controller keeps everything consistent and prevents confusion.

from model import Game_State, PlayerData
from net import udp #Caleb added

# This is the app's only shared game state.
# Everyone will read & write through this object.
state = Game_State()


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
    recordLog("The Game is now in the " + str(phase) + " phase.")


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
    This will store the player in the correct roster (red/green).
    Later, this will also trigger the UDP broadcast of equipmentID.
    """

    capitalTeamname = str(team).upper() #Converts the team names to Uppercase so inputs can be compared easily

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
    # Since this is Week 1, there is no real UDP yet, so we call a "Net Stub" = "Networking Stub".
    netBroadcastEquipment(equipmentID) 

# -------------------------------------------------
# These are the Stubs (placeholders) for Sprint 2 
# -------------------------------------------------
#
# A "stub" is a fake function that is created so our program doesn't crash.
# That way the UI and controller code run before the all of the database/UDP code is finished.
#
# Later, this is where Caleb will plug in the socket code.
# For now, I will log the expected behavior of these functions.

def dbGetCodename(playerID):
    """
    Database Stub:
    Later on, Will is gonna search the PostgreSQL table and return a codename.

    the return format should look like:
    - (True, "Codename") if found
    - (False, None) if not found
    """
    return (False, None)


def dbInsertPlayer(playerID, codename):
    """
    Database Stub:
    
    Here Will is gonna insert a new player into the database.
    At this moment the action is logged so there's no crashes.
    """
    recordLog("The player " + str(playerID) +
               " is inserted with codename " + str(codename))


def netSetIp(ip):
    """
    Network Stub:
    Later on, Caleb is gonna store the IP and use it for UDP sockets.
    But for right now let's just log it.
    """
    udp.netSetIp(ip)
    recordLog("The network IP is set to " + str(ip))


def netBroadcastEquipment(equipmentID):
    """
    Network Stub:
    Here, Caleb will send the equipmentID out on UDP broadcast port 7500.
    For right now, let's just log what would be broadcast.
    """
    udp.netBroadcastEquipment(equipmentID)
    recordLog("This equipment ID " + str(equipmentID) + " would be broadcast.")


def netBeginUDP_Listener():
    """
    Network Stub:
    Caleb will listen for hits after opening the UDP receive port 7501.
    For right now, let's log the fact that we start listening here.
    """
    udp.netBeginUDP_Listener(recordLog)
    recordLog("UDP Listener started on port 7501")


# # -----------------------------
# # Test Controller.py
# # To Run type python3 controller.py
# # -----------------------------
# if __name__ == "__main__":
#     clearItAll()
#     addPlayerToTeam("RED", 1, "Mordecai", 112)
#     addPlayerToTeam("GREEN", 2, "Rigby", 208)

#     print("The controller test was a success.")
#     print("The size of the Red team:", len(state.redTeam))
#     print("The size of the Green team:", len(state.greenTeam))
#     print("Here's the Log lines:", len(state.eventLog))


# -----------------------------
# Caleb  Integration Test
# To Run type: python controller.py in one terminal. In another terminal, type : 
# python -c "import socket; sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); sock.sendto(b'53', ('127.0.0.1', 7501)); print('Hit sent!')"
# -----------------------------
if __name__ == "__main__":
    import time
    
    print("--- 1. Testing System Reset ---")
    clearItAll()

    print("--- 2. Starting UDP Listener (Check for 'UDP received' messages) ---")
    # This connects the network listener to the event log!
    netStartUDP_Listener()

    print("--- 3. Testing Player Add & Broadcast ---")
    # This should trigger a broadcast on port 7500
    addPlayerToTeam("RED", 1, "Mordecai", 112)
    
    print("--- SYSTEM IS LIVE ---")
    print("Waiting for hits on Port 7501...")
    print("Press Ctrl+C to stop.")
    
    # Keep the program alive so the background thread can listen
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTest finished.")
        # Print the log to prove the Controller 'heard' the network
        print("Final Event Log:", state.eventLog)
