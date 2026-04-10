#!/bin/bash

source ./lib/setenv-bsd-freebsd.sh
echo
if [ "$(pwd | grep '/usr/local/share/themes/Xfce Evolution')" -o "$(pwd | grep '/usr/share/themes/Xfce Evolution')" ]
then
  echo "Cannot run uninstaller for all users."
  echo "In order to remove the 'Xfce Evolution'-specific system tuning for all users you must completely uninstall 'Xfce Evolution' BY USING YOUR PACKAGE MANAGER."
  if [ -d $themes_dir_user/'Xfce Evolution' ]
  then
    echo
    echo "FYI"
    echo "---"
    echo "The 'Xfce Evolution' theme files appear to also be installed for your own user ('`whoami`'). You can remove the 'Xfce Evolution'-specific system tuning for your own user by running this uninstaller from '$themes_dir_user/Xfce Evolution/TOOLS/SETUP/'."
  fi
  source ./lib/abort-common.sh
fi

#if [ ! "$(pwd | grep $themes_dir_user/'Xfce Evolution')" ]
#then
#  echo "Cannot run uninstaller from this location."
#  echo "You must run this uninstaller from your own user's themes folder '$themes_dir_user/Xfce Evolution/TOOLS/SETUP/'."
#  source ./lib/abort-common.sh
#fi

test "$(exec_input "Setup will remove the 'Xfce Evolution'-specific system tuning for YOUR OWN USER ('`whoami`'), if any. Continue (y/N)?" y n)" != "y" && source ./lib/abort-common.sh
echo
source ./lib/remove_qt_fix-common.sh "./lib/su-bsd-freebsd.sh" "user"
if [ -d $themes_dir_system/'Xfce Evolution' ]
then
  echo "FYI"
  echo "---"
  echo "The 'Xfce Evolution' theme appears to also be installed for all users. If you'd like to remove the 'Xfce Evolution'-specific system tuning for all users then you must completely uninstall 'Xfce Evolution' BY USING YOUR PACKAGE MANAGER."
  echo
fi
source ./lib/done-common.sh
