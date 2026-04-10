#!/bin/bash

echo
if [ -d '/usr/local/share/themes/Xfce Evolution' -o -d '/usr/share/themes/Xfce Evolution' ]
then
  echo "Cannot run installer."
  echo
  echo "The 'Xfce Evolution' theme appers to be installed for all users, in themes folder '/usr/local/share/themes' and/or '/usr/share/themes'. All 'Xfce Evolution'-specific system tuning an dependencies should be already installed."
  echo
  echo "If you beleive (some of) the dependencies are not properly installed, then you should uninstall 'Xfce Evolution' from your system BY USING YOUR PACKAGE MANAGER and then re-install it."
  echo
  echo "You can re-install 'Xfce Evolution' for all users BY USING YOUR PACKAGE MANAGER, or you can install it for your own user by extracting AT LEAST the 'Xfce Evolution' folder from the 'xfce-evolution-n.n.n.zip' archive into your own user's themes folder '$themes_dir_user', and then run this installer for your own user from folder '$themes_dir_user/Xfce Evolution/TOOLS/SETUP/'"
  source ./lib/abort-common.sh
elif [ -d $themes_dir_user/'Xfce Evolution' ]
then
  if [ "$(pwd | grep $themes_dir_user/'Xfce Evolution')" ]
  then
    source ./lib/su-bsd-freebsd.sh "user"
  else
    echo "Cannot run installer from this location."
    echo "You can run the installer for your own user, from '$themes_dir_user/Xfce Evolution/TOOLS/SETUP/'"
    source ./lib/abort-common.sh
  fi
else
  echo "Cannot run installer."
  echo "The 'Xfce Evolution' theme files appear to NOT be installed on your system."
  echo "You can either install 'Xfce Evolution' for all users BY USING YOUR PACKAGE MANAGER, or you must extract AT LEAST the 'Xfce Evolution' folder from the 'xfce-evolution-n.n.n.zip' archive into your own user's themes folder '$themes_dir_user', and then run this installer for your own user from '$themes_dir_user/Xfce Evolution/TOOLS/SETUP/'"
  source ./lib/abort-common.sh
fi

test "$(exec_input "Setup will install the 'Xfce Evolution'-specific system tuning for YOUR OWN USER ('`whoami`'). Continue (y/N)?" y n)" != "y" && source ./lib/abort-common.sh
echo
