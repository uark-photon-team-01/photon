# The Internals (Team Interfaces)
This file contains all of the names/fields/events that way everyone’s code matches.

If you change a name in code later that is fine, just update this file as well.

---

##  Player fields - PlayerData

Fields:
- playerID (int) - This is the player’s ID number from the database
- codename (str) - This will be the player codename
- equipmentID (int) - This is the equipment ID the player is using
- team (str) - must be "RED" or "GREEN"
- score (int) - begins at 0
- has_baseIcon (bool) - This is True if base icon should be next to the name

---

## Game state fields - GameState

Fields:
- redTeam (list[PlayerData]) - The red team's roster
- greenTeam (list[PlayerData]) - The green team's roster
- phase (str) - This is the current app phase/screen (example: "Splash", "Beginning", "Playing")
- time_remaining (int) - How much time left in seconds. Useful for the countdown/game timer.
- eventLog (list[str]) - The event log lines

---

## Event format (Network -> Game Logic -> UI)
The Network code will receive text from the UDP and convert it into simple events.
The controller/game logic should be able to handle these events.

### TAG event
When a tag happens (normal hit i.e. one player just shot another player):
- type: "TAG"
- transmitterID: int
- hitID: int

Here's an Example:
{ "type": "TAG", "transmitterID": 115, "hitID": 666 }

### BASE event
When a base score code is received (i.e. a player shot the enemy's base):
- type: "BASE"
- code: int (43 for green base scored, 53 for red base scored)
- transmitterID: int (may not be needed)

Here's an Example:
{ "type": "BASE", "code": 53 }

### SYSTEM event (broadcast codes)
These are special codes that must be broadcast by our software:
- 202 = broadcast when the game countdown finishes (the game begins)
- 221 = broadcast 3 times when the game ends

Example:
{ "type": "SYSTEM", "code": 202 }

### Network defaults 
- Default IP: 127.0.0.1
- Broadcast port: 7500
- Receive port: 7501

---

## Controller functions (these can be called by the UI)

The database or network should not call the UI directly
UI can only call the controller functions

Required function names (these must exist for our program):
- grabState()
- changePhase(phase)
- recordLog(message)
- clearItAll()
- addPlayerToTeam(team, playerID, codename, equipmentID)

Stubs / placeholder functions (The Database & Network will fulfill these later):
- dbGetCodename(playerID) -> this returns (Bool_found, codename_empty_or_not)
- dbInsertPlayer(playerID, codename)
- netSetIp(ip)
- netBroadcastEquipment(equipmentID)
- netBeginUDP_Listener()
