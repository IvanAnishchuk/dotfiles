#!/bin/bash

echo
if [ -d $themes_dir_user/'Xfce Evolution' -a -d $themes_dir_system/'Xfce Evolution' ]
then
  echo "FYI"
  echo "---"
  test "$(exec_input "The 'Xfce Evolution' theme files apper to be installed both for your own user ('`whoami`') in themes folder '$themes_dir_user', and for all users in themes folder '$themes_dir_system'. For system management reasons, it is advisable to keep only one installation on your system. Exit setup? (Y/n)" y n)" != "n" && ./lib/abort-common.sh
  echo
fi

if [ "$(pwd | grep $themes_dir_user/'Xfce Evolution')" ]
then
  user_text="YOUR OWN USER ('`whoami`')"
  source ./lib/su-linux.sh "user"
elif [ "$(pwd | grep $themes_dir_system/'Xfce Evolution')" ]
then
  user_text="ALL USERS"
  source ./lib/su-linux.sh "system"
else
  echo "Cannot run installer from this location."
  echo "Make sure you have extracted AT LEAST the 'Xfce Evolution' base theme folder from the 'xfce-evolution-n.n.n.zip' archive into one of your themes folders (i.e. in '$themes_dir_user' for your own user, or in '$themes_dir_system' for all users), and then run this installer from your themes folder (from sub-folder 'Xfce Evolution/TOOLS/SETUP')."
  source ./lib/abort-common.sh
fi

test "$(exec_input "Setup will install the 'Xfce Evolution'-specific system tuning for $user_text. Continue (y/N)?" y n)" != "y" && source ./lib/abort-common.sh
echo
