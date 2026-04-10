#!/bin/bash

source ./lib/setenv-bsd-freebsd.sh # initialize env vars and funcs

# "$sudo" prefix will be used for all operations which can be performed as either current user or as root
if [ "$1" == "user" ]
then
  sudo="eval "
elif [ "$1" == "system" ] # never gets here in this version
then
  sudo='su -m root -c bash -c '
elif [ "$(exec_input "Setup 'Xfce Evolution' for your own [u]ser or for [a]ll users? (a/U)" a u)" == "a" ] # never gets here in this version
then
  sudo='su -m root -c bash -c '
else
  sudo="eval "
fi

source ./lib/setenv-bsd-freebsd.sh # some env depend on the selections above, so re-evaluate
