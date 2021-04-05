#!/bin/bash
set -e

#sudo apt update && sudo apt upgrade -y && sudo apt autoremove -y


cd ~/new
sudo apt install python3.9-dev python3-pip python3.9-distutils libgl1-mesa-glx -y
python3.9 -m pip install -U pip
python3.9 -m pip install -U sphinx
python3.9 -m pip install  -r containers/user/sources/requirements.txt
cd containers/database/mariadb/ && python3.9 configure.py --init --create
