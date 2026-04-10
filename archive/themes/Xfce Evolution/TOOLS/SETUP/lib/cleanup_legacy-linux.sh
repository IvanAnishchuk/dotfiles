#!/bin/bash

# this script is always run in a root _sub-shell_, so must re-define the env
source ./lib/setenv-linux.sh

# remove old version of system-wide 'QT_QPA_PLATFORMTHEME', and old version of 90-qt5.conf for both own-user and all-users (possible leftovers from previous versions)
### this section will eventually be romeved ###
echo
echo "Cleaning up legacy settings..."
rm -f ~/.config/fontconfig/conf.d/90-qt5.conf
rm -f /etc/fonts/conf.d/90-qt5.conf
test -f /etc/environment && exec_delines '#xfce-evolution' /etc/environment
