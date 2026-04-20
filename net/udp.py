"""
Hey Caleb! This starter code is based on Jim's Starter code.

The following was specifically pulled from Jim:
- udp_files/python_udpclient.py
    - The creation of the UDP socket (AF_INET, SOCK_DGRAM)
    - set the SO_BROADCAST
    - Be sure to send to (message, (ip, port))
- udp_files/python_udpserver.py
    - The creation of the UDP socket (AF_INET, SOCK_DGRAM)
    - bind the fillowing (("0.0.0.0", port))  # with this you can listen on any IP
    - Do this: recvfrom(buffer) loop
- udp_files/python_trafficgenarator_v2.py (This is just a reference for the format)
    - It should show messages like "transmitterID:hitID" and special codes like 43/53

Requirements for Sprint 2 this file must support:
- Use localhost (127.0.0.1) by default
- Broadcast on port 7500
- Receive on port 7501 (bind to 0.0.0.0)
- Provide a way to change the network IP
- After each player addition, controller will call netBroadcastEquipment(equipmentID)

Important Info:
- This file should not be directly called by the UI
- The Controller will call this file.
- This starter cide is kinda minimal it just sets up the network to send, receive, print.
"""

"""
=========================================================
NETWORK ARCHITECTURE & HARDWARE TESTING
=========================================================
Ports & Routing:
- Broadcast/Client Traffic: Port 7500
- Listener: Port 7501 (Binds to 0.0.0.0 to accept from any IP)
- Changing the "Broadcast IP" in the UI ONLY changes the client destination. 
  It does not alter the listener address.

Instructor Traffic Generator:
- Waits for code 202 (Game Start) to begin sending gameplay traffic.
- Stops sending traffic when it receives code 221 (Game End).

TESTING CHECKLIST (Run via netcat in Terminal B):
Setup: IP = 127.0.0.1. 
Red Team: Spiderman (ID 1, Eq 11), Batman (ID 2, Eq 22). 
Green Team: Wolverine (ID 3, Eq 33).

1. Opponent Tag (11:33) -> Spiderman gets 10 pts, Red gets 10 pts.
   Command: echo -n "11:33" | nc -u -w1 127.0.0.1 7501
   
2. Same-Team Tag (11:22) -> Spiderman & Batman both LOSE 10 pts. Red drops 20 pts.
   Command: echo -n "11:22" | nc -u -w1 127.0.0.1 7501
   
3. Red Base Score (11:43) -> Spiderman gets 100 pts + Base Icon. Red gets 100 pts.
   Command: echo -n "11:43" | nc -u -w1 127.0.0.1 7501
   
4. Green Base Score (33:53) -> Wolverine gets 100 pts + Base Icon. Green gets 100 pts.
   Command: echo -n "33:53" | nc -u -w1 127.0.0.1 7501

5. Invalid Data ("hello" or "9999") -> Ignored, prints warning. No crash.
6. Unknown Transmitter ("99:33") -> Ignored, error logged.
7. Self-Tag ("11:11") -> Ignored, error logged.
8. Pre-Game Event -> Ignored if the game is in WARNING or ENDED phase.
"""


import socket
import threading
import time

def parse_packet(raw_text):
    """Converts a raw UDP string into an event dictionary."""
    text = str(raw_text).strip()
    
    # Check for empty string or missing colon
    if not text or ":" not in text:
        return None
        
    parts = text.split(":")
    if len(parts) != 2:
        return None
        
    # Make sure both parts are actual numbers
    try:
        transmitter = int(parts[0].strip())
        hit = int(parts[1].strip())
    except ValueError:
        return None
        
    # Check if it's a base code (43 for red, 53 for green)
    if hit in (43, 53):
        return {"type": "BASE", "transmitter": transmitter, "hit": hit}
        
    # Otherwise, it's a normal player tag
    return {"type": "TAG", "transmitter": transmitter, "hit": hit}

#The Required Ports
broadcastPort = 7500
receivePort = 7501
bufferSize = 1024

#The Default network address
networkIP = "127.0.0.1"

# Keep a reusable sender socket 
senderSocket = None


def netSetIp(ip):
    """
    This function should allow the changing of the network address.
    If a user selects a different network address, then the Controller/UI will call this.
    """
    global networkIP
    networkIP = str(ip).strip()
    print(f" The UDP network IP set to {networkIP}")


def netBroadcastEquipment(equipmentID):
    """
    This function should broadcast equipment codes on UDP port 7500.
    This is from Jim's python_udpclient.py
    This can also be 202 or 221, signaling 'Game Start' or 'Game End'
    """
    global senderSocket

    # This is the creation of the client socket creation
    if senderSocket is None:
        senderSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        senderSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # this is here since the format of transmission should be a single integer
    message = str(int(equipmentID)).encode("utf-8")
    senderSocket.sendto(message, (networkIP, broadcastPort))

    print(f"UDP Broadcast sent: {equipmentID} to {networkIP}:{broadcastPort}")


def netBeginUDP_Listener(newMessage=None):
    """
    This function starts a UDP receive socket on port 7501.

    The purpose of the newMessage callback:
    - This is an optional function passed by the controller.
    - We parse the raw UDP text and call newMessage(parsed_event) 
      every time a valid TAG or BASE event is received.
    """

    def listenLoop():
        # This is the cration of the server socket
        rxSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # The following will allow the binding to any IP
        try:
            rxSocket.bind(("0.0.0.0", receivePort))
            print("The UDP listener is running on 0.0.0.0:" + str(receivePort))
        except OSError as e:
            print(f"Warning: Could not bind to port {receivePort}. Is the listener already running? Error: {e}")
            return  # This stops the thread from crashing the whole app

        while True:
            data, addr = rxSocket.recvfrom(bufferSize)
            raw = data.decode("utf-8", errors="ignore").strip()

            # Here, the receieved data is printed 
            print("UDP received:", raw, "from", addr)

            # Parse the raw data
            parsed_event = parse_packet(raw)
            
            if parsed_event is None:
                print(f"Warning: Invalid UDP packet ignored -> {raw}")
                continue # Skip the rest of the loop, don't send to controller

            # With this the Controller can optionally handle it
            if newMessage is not None:
                newMessage(parsed_event) # Send the DICTIONARY, not the raw string!

    # With this thread the UI should not feeeze
    # target=listenLoop means “Run listenLoop() in a background thread”
    # daemon=True means “when the app closes, KILL this thread”
    threading.Thread(target=listenLoop, daemon=True).start()


# -----------------------------
# Quick testing for Week 1
# -----------------------------
if __name__ == "__main__":
    # Here the listener is starting & should print whatever it received on the 7501
    netBeginUDP_Listener()

    # This is a test message sent on the 7500
    print("Test broadcast 123 is sent.")
    netBroadcastEquipment(123)

    # This just keeps the listener running
    # This loop keeps the file alive so you can test traffic, press keys, and whatever else.
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt: # this what happens when you press Ctrl+C to stop the program.
        print("The listener has stopped.")

