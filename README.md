**How to run the program 101**
-----

Follow these commands EXACTLY (ignore the parentheses)

To log into the Virtual Machine type "student" for the username and password, afterwards pressing enter.
Then, once you are in press the "Terminal Emulator" (Bottom of the screen)

1. cd ~ (Go Home)
2. sudo apt-get update (Install basic tools)
It will ask the password for student type "student" (ignore the air quotes).
3. sudo apt-get install -y git python3 python3-pip python3-tk netcat-openbsd
4. git clone https://github.com/uark-photon-team-01/photon.git (Clone our repo)
5. cd ~/photon
6. ls
7. bash install.sh
8. python3 main.py
   



**IMPORTANT INFO**

- For some reason when starting the app not all of the widgets are drawn, just drag the window and resize it so everything fits.
- when you drag the game window Linux/VirtualBox sends a fresh repaint event, which forces all widgets to draw.
- NOTE: This doesn't always occur when first starting the game. Sometimes everything just loads automatically.

#
Test network code 

In Terminal A type
cd ~/photon
pkill -f "python3 main.py" 2>/dev/null || true
clear
python3 main.py

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
  





