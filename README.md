**How to run the program 101**
-----



**To run the install script, type the following into the command line:**

- bash install.sh

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
  





