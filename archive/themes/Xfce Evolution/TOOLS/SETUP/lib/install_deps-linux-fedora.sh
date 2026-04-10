#!/bin/bash

# this script is always run in a root _sub-shell_, so must re-define the env
source ./lib/setenv-linux.sh

echo "Installing/updating dependencies..."
echo

#install gtk2 murrine engine
sudo yum -y install gtk-murrine-engine

# install qt5 style plugins (qt5+)
sudo yum -y install qt5-qtstyleplugins

# install Nemo FM
echo
if [ "$(exec_input "Install/update optional 'Nemo' file manager? (y/N)" y n)" == "y" ]
then
  sudo yum -y install nemo
fi
