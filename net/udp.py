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

import socket
import threading
import time

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
    This function should start a UDP receive socket on port 7501.

    The purpose of the newMessage:
    - This is an optional function passed by controller
    - we call newMessage(rawText) every time data is recieved. 

    Caleb you need to:
    - Make sure messages like "transmitterID:hitID" are received -- Caleb: They are recieved
    - later on, you can parse and convert these into to TAG/BASE events 
    """

    def listenLoop():
        # This is the cration of the server socket
        rxSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # The following will allow the binding to any IP
        rxSocket.bind(("0.0.0.0", receivePort))

        print("The UDP listener is running on 0.0.0.0:" + str(receivePort))

        while True:
            data, addr = rxSocket.recvfrom(bufferSize)
            raw = data.decode("utf-8", errors="ignore").strip()

            # Here, the receieved data is printed 
            print("UDP received:", raw, "from", addr)

            # With this the Controller can optionally handle it
            if newMessage is not None:
                newMessage(raw)

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

