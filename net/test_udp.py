import udp
import socket
import time

# --- TEST 1: SIMULATING THE CONTROLLER ---
# This mimics what the Controller will do: define a function to handle incoming hits
def mock_controller_handle_message(message):
    print(f"[CONTROLLER] Great! I received this data from the network: {message}")

print("--- STARTING TEST ---")

# 1. Start your listener (Passing our fake controller function)
print("1. Starting the UDP Listener...")
udp.netBeginUDP_Listener(mock_controller_handle_message)

# --- TEST 2: SIMULATING THE HARDWARE (VESTS) ---
# We will create a "Fake Vest" to shoot data at your listener
print("2. Simulating a 'Hit' from a vest...")
fake_vest_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Send a standard hit "Player 4 hit Player 2" to port 7501
fake_vest_socket.sendto(b"4:2", ("127.0.0.1", 7501))

# Wait a second to let the message arrive
time.sleep(1)

# --- TEST 3: TESTING BROADCAST (GAME START) ---
# We need to see if your broadcast actually sends data out to port 7500
print("3. Testing Broadcast (Sending Game Start Code 202)...")

# First, we need to listen on 7500 to catch what you send
fake_vest_receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
fake_vest_receiver.bind(("127.0.0.1", 7500))
fake_vest_receiver.settimeout(2) # Don't wait forever

# Now, call your function to send the code
udp.netBroadcastEquipment(202)

try:
    data, addr = fake_vest_receiver.recvfrom(1024)
    print(f"[VEST] Success! I received command code: {data.decode()}")
except socket.timeout:
    print("[VEST] Failed: I didn't hear anything on port 7500.")

print("--- TEST COMPLETE ---")