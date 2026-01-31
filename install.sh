#!/usr/bin/env bash
set -e 

echo "The following above means 'run this file with bash.'"
echo "Set -e means 'stop if any command fails.'"


echo "Updating package list."
sudo apt-get update

echo "Automatically installing python, Tkinter GUI support,"
echo "PostgreSQL Driver, and the package installer (for extra liberies)."
sudo apt-get install -y python3 python3-tk python3-psycopg2 python3-pip

echo "Install complete."
echo "To run this project, please use the following command: python3 main.py"
