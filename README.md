**How to run the program 101**
-----

Follow these commands EXACTLY (ignore the parentheses)

To log into the Virtual Machine type "student" for the username and password, afterwards pressing enter.
Then, once you are in press the "Terminal Emulator" (Bottom of the screen) (Section A)

cd ~ 
sudo apt-get update 

It will ask the password for student type "student" (ignore the air quotes).

sudo apt-get install -y git python3 python3-pip python3-tk netcat-openbsd
git clone https://github.com/uark-photon-team-01/photon.git 
cd ~/photon
ls
bash install.sh

Before you run anyhting, make sure to pull the latest code (Section B)

cd ~/photon
git checkout main
git fetch origin
git reset --hard origin/main
git clean -fd
git rev-parse --short HEAD

If internet/DNS breaks (git pull says “Could not resolve host”), type in the following (Section C).

After entering in this code, pull the latest code again. (Section B)

sudo bash -c 'cat > /etc/resolv.conf <<EOF
nameserver 8.8.8.8
nameserver 1.1.1.1
EOF'

Before you start the game, let's clear the database (Section D)
This count should be zero after entering these commands.

sudo systemctl start postgresql
PGPASSWORD=student psql -h localhost -U student -d photon -c "CREATE TABLE IF NOT EXISTS players (id INTEGER PRIMARY KEY, codename VARCHAR(255));"
PGPASSWORD=student psql -h localhost -U student -d photon -c "TRUNCATE TABLE players;"
PGPASSWORD=student psql -h localhost -U student -d photon -c "SELECT COUNT(*) FROM players;"

Now terminate old processes and run the program (Section E)

cd ~/photon
pkill -f "python3 main.py" 2>/dev/null || true
python3 main.py

**IMPORTANT INFO**

- For some reason when starting the app not all of the widgets are drawn, just drag the window and resize it so everything fits.
- when you drag the game window Linux/VirtualBox sends a fresh repaint event, which forces all widgets to draw.
- NOTE: This doesn't always occur when first starting the game. Sometimes everything just loads automatically.

#
Test network code 

In Terminal A type
- cd ~/photon
- pkill -f "python3 main.py" 2>/dev/null || true
- clear
- python3 main.py

-You should see one listener line for this run

Add a Player then verify the broadcast
In the game add a player for the red team, afterwards you should see a broadcast line in Terminal A.

Force a receive line in the terminal
In terminal B type: echo -n "TEST123" | nc -u -w1 127.0.0.1 7501
Back in Terminal A, you should see received line now! Yay.

Confirm an ene-to-end IP change
In the game, change the Network IP to 127.0.0.2, then click Set Network IP
Add a player for the red team.

Terminal A should show: IP change line & a broadcast line now using 127.0.0.2:7500




#


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


**Team Info: Github    &    Real Names**

CentariB      
- Centarrius Brooks

WillBoone24
- Will Boone

EmmaMah258
- Emma Mahaffey

CollegeBoundCaleb
- Caleb Carpenter
  





