**How to run the program 101**
-----

**Follow these commands EXACTLY** (ignore the air quotes)

To log into the Virtual Machine type "student" for the username and password, afterwards pressing enter.

Then, once you are in press the "Terminal Emulator" (Bottom of the screen) 

-----

**Setup Up The Program (Section A)**

Enter the following lines of code. (You can just copy and paste these lines).

Ignore the numbers please.

1. cd ~ 
2. sudo apt-get update 

It will ask the password for student type "student" (ignore the air quotes).

3.  git clone https://github.com/uark-photon-team-01/photon.git 
4. cd ~/photon
5. bash install.sh

-----

**Before you run anything, make sure to pull the latest code (Section B)**

1. git checkout main
2. git fetch origin
3. git reset --hard origin/main
4. git clean -fd
5. git rev-parse --short HEAD

-----

**If internet/DNS breaks (git pull says “Could not resolve host”), type in the following. (Section C).**

After entering in this code, pull the latest code again. (Section B)

1. sudo bash -c 'cat > /etc/resolv.conf <<EOF
2. nameserver 8.8.8.8
3. nameserver 1.1.1.1
4. EOF'

-----

**Start PostgreSQL and check the provided database (Section D)**

Open a second terminal and type in the code below.

1. sudo systemctl start postgresql

It will ask the password for student type "student" (ignore the air quotes). Also, use the provided database as-is. Do not create, alter, or truncate the table.


2. psql -d photon -c "\dt"
3. psql -d photon -c "\d players"
4. psql -d photon -c "SELECT * FROM players ORDER BY id;"
5. psql -d photon -c "SELECT COUNT(*) FROM players;"

Commands explained:

- \dt: shows the tables in the database
- \d players: shows the structure of the players table
- SELECT * FROM players ORDER BY id; prints the current contents already in the database
- SELECT COUNT(*) FROM players; shows how many player rows currently exist

-----

**Now terminate old processes and run the program (Section E)**

Go back to the first Terminal and enter the following:

1. pkill -f "python3 main.py" 2>/dev/null || true
2. python3 main.py

----- 

**IMPORTANT INFO**

- For some reason when starting the app not all of the widgets are drawn, just drag the window and resize it so everything fits.
- When you drag the game window Linux/VirtualBox sends a fresh repaint event, which forces all widgets to draw.
- NOTE: This doesn't always occur when first starting the game. Sometimes everything just loads automatically.

#
**Test network code**

NOTE: Terminal A is your original terminal.

(If you already have just done Section E just ignore this code below)

In Terminal A type:
- cd ~/photon
- pkill -f "python3 main.py" 2>/dev/null || true
- clear
- python3 main.py

You should see one listener line for this run in Terminal A.

-----



**Add a Player then verify the broadcast**

In the game, add a player for the red team, afterwards you should see a broadcast line in Terminal A.

-----

**Force a receive line in the terminal**

In terminal B type: 
- echo -n "TEST123" | nc -u -w1 127.0.0.1 7501

Back in Terminal A, you should see received line now.

-----


**Confirm an end-to-end IP change**

In the game, change the Network IP to 127.0.0.2, then click Set Network IP. Now Add a player for the red team.

Terminal A should show: IP change line & a broadcast line now using 127.0.0.2:7500

Now you know that the network code works properly.


## Network / Gameplay Test Checklist

### Before You Start
Use this exact setup so all of the tests make sense.

**Network IP**
- Set the Network IP to `127.0.0.1` before running the main UDP gameplay tests.

**Roster Setup**
Add these players before pressing F5:

**Red Team**
- Spiderman — Player ID 1, Equipment ID 11
- Batman — Player ID 2, Equipment ID 22

**Green Team**
- Wolverine — Player ID 3, Equipment ID 33

Make sure all equipment IDs are unique.

This setup lets us test:
- opponent tag = `11:33`
- same-team tag = `11:22`
- red-team base score = `11:43`
- green-team base score = `33:53`

---

### 1. Start the Game
In Terminal A:
1. Run the program
2. Add the players listed above
3. Press **F5**
4. Wait for the 30-second warning to finish
5. When the game says **Game On!**, start the UDP tests below

---

### 3. Test a Valid Opponent Tag
In Terminal B, run:

- echo -n "11:33" | nc -u -w1 127.0.0.1 7501

Spiderman tags Wolverine.

Spiderman gains 10 points.

Red team total increases by 10.


### 4. Test a Same-Team Tag


In Terminal B, run:

- echo -n "11:22" | nc -u -w1 127.0.0.1 7501

Spiderman hits Batman on the same team.

Spiderman loses 10 points.

Batman loses 10 points.

Red team total drops by 20.

### 5. Test a Valid Red Base Score (Code 43)

In Terminal B, run:

- echo -n "11:43" | nc -u -w1 127.0.0.1 7501

Spiderman scores on the green base.

Spiderman gains 100 points.

Red team total increases by 100.

A base icon appears next to Spiderman.


### 6. Test a Valid Green Base Score (Code 53)

In Terminal B, run:

- echo -n "33:53" | nc -u -w1 127.0.0.1 7501

Wolverine scores on the red base.

Wolverine gains 100 points.

Green team total increases by 100.

A base icon appears next to Wolverine.


### 7. Test Invalid Data (Garbage Text)

In Terminal B, run:

- echo -n "hello" | nc -u -w1 127.0.0.1 7501

The program does not crash.

- Terminal A prints:
- Warning: Invalid UDP packet ignored -> hello

No score changes.

No team total changes.

### 8. Test Invalid Data (Missing Separator)

In Terminal B, run:

- echo -n "9999" | nc -u -w1 127.0.0.1 7501

The program does not crash.

- Terminal A prints:
- Warning: Invalid UDP packet ignored -> 9999

- No score changes.

- No team total changes.

### 9. Test an Unknown Transmitter


In Terminal B, run:

- echo -n "99:33" | nc -u -w1 127.0.0.1 7501

The event is ignored.

Terminal A / game log shows an unknown transmitter error.

No score changes.

No team total changes.

### 10. Test a Self-Tag

In Terminal B, run:

- echo -n "11:11" | nc -u -w1 127.0.0.1 7501

The event is ignored.

Terminal A / game log shows a self-tag error.

No score changes.

No team total changes.


### 11. Test an Event Before PLAYING Phase

Run this before pressing F5, or during the 30-second warning:

- echo -n "11:33" | nc -u -w1 127.0.0.1 7501

The event is ignored.

The game log says the event was ignored because the game is not in the PLAYING phase.

No score changes.

No team total changes.


### 12. Verify Scheduled Game Broadcasts (202 and 221)**

- Game Start (202): When that 30-second warning countdown finishes, check Terminal A. You should see a line saying: UDP Broadcast sent: 202 to 127.0.0.1:7500.
- Game End (221): Let the 6-minute game clock completely run out. Once it hits zero, Terminal A should print UDP Broadcast sent: 221 to 127.0.0.1:7500 exactly three times.



#
**Look at the Database during runtime**

You should already have two terminals open.

Terminal A will run the app (python3 main.py)

Terminal B will run SQL checks (psql commands)

In Terminal B, you can inspect the existing database contents at any time with:

- psql -d photon -c "SELECT * FROM players ORDER BY id;"
- psql -d photon -c "SELECT COUNT(*) FROM players;"



Now close the app please.

-----

**In Terminal A, Start the App**

Please enter the following code:
- cd ~/photon
- pkill -f "python3 main.py" 2>/dev/null || true
- python3 main.py

-----


Now you know that the database code works properly.

-----


**Use this command to run the program**

- python3 main.py

#


**Your virtual machine should automatically install Tkinter when you run install.sh.**

**In case Tkinter does not install after running the install script, input the following into the command line:**

- sudo apt-get update

- sudo apt-get install -y python3-tk

#


**Structure of our Repo**

main.py 
- Starts the whole app

- When python3 main.py is ran, this file runs first. 

- This creates the main window to decide which screen is shown (splash -> entry -> game).


install.sh 
- Setup script 

- This script installs needed software/packages for the program. 

- It may also tell the user what exactly is required for the program to run.


db/ 
- This is the location of the database code (PostgreSQL)


ui/ 
- This is the location of the screen/window code (how the app looks)


net/ 
- This is the location of the network code


assets/ 
- This is the location of the images and audio files.

  #


## Team Info: GitHub and Real Names

| GitHub Username   | Real Name          |
|-------------------|--------------------|
| CentariB          | Centarrius Brooks  |
| WillBoone24       | Will Boone         |
| EmmaMah258        | Emma Mahaffey      |
| CollegeBoundCaleb | Caleb Carpenter    |




