import tkinter as tkr #built-in python library for making user windows

window = tkr.Tk() #the main window object
window.title("Repo Skeleton Test") #This .title comes from the window object in Tkinter
#.Label & .pack are Tkinter methods. 
#.Label() is a widget class
#.pack() is a layout method to place things & is a part of the Label widget object
#padx & pady is just whitespace around the text from the edge of the window
tkr.Label(window, text = "Hey Ya! This Repo skeleton is good to go.").pack(padx=25, pady=25)
window.mainloop() #starts an event loop to keep the app running until a user quits.
