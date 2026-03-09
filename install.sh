#!/usr/bin/env bash
set -e

echo "The line above means: run this file with bash."
echo "set -e means: stop if any command fails."

echo "Updating package list..."
sudo apt-get update

echo "Installing required packages..."
sudo apt-get install -y git python3 python3-tk python3-psycopg2 python3-pip python3-pil python3-pygame

echo "Install complete."
echo "To run the project:"
echo "  1. sudo systemctl start postgresql"
echo "  2. python3 main.py"
