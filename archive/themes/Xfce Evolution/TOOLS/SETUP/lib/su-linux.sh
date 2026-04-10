#!/bin/bash

source ./lib/setenv-linux.sh # initialize env vars and funcs

# "$sudo" prefix will be used for all operations which can be performed as either current user or as root
if [ "$1" == "user" ]
then
  sudo="eval "
elif [ "$1" == "system" ]
then
  sudo="sudo bash -c "
elif [ "$(exec_input "Setup 'Xfce Evolution' for your own [u]ser or for [a]ll users? (a/U)" a u)" == "a" ] # never gets here in this version
then
  sudo="sudo bash -c "
else
  sudo="eval "
fi

source ./lib/setenv-linux.sh # some env depend on the selections above, so re-evaluate
