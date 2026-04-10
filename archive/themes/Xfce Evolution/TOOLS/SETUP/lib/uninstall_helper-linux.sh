#!/bin/bash

source ./lib/setenv-linux.sh
if [ "$(pwd | grep $themes_dir_user/'Xfce Evolution')" ]
then
  u="o"
elif [ "$(pwd | grep $themes_dir_system/'Xfce Evolution')" ]
then
  u="a"
else
  echo
  echo "WARNING"
  echo "-------"
  echo "You are not running setup from an 'Xfce Evolution' installation folder."
  test "$(exec_input "It is advisable to exit setup now, and then run setup specifically for your own user from folder '$themes_dir_user/Xfce Evolution/TOOLS/SETUP/', and/or for all users from folder '$themes_dir_system/Xfce Evolution/TOOLS/SETUP/' (depending on your current installation(s)). However, you can also continue with setup and explicitly choose your uninstall options. Continue? (y/N):" y n)" != "y" && source ./lib/abort-common.sh
  echo
  u="$(exec_input "Setup can remove the 'Xfce Evolution'-specific system tuning for your [o]wn user ('`whoami`'), for [a]ll users, or [b]oth (o/a/B):" o a b)"
fi
if [ "$u" == "o" ]
then
  user_text="YOUR OWN USER ('`whoami`')"
elif [ "$u" == "a" ]
then
  user_text="ALL USERS"
else # default
  user_text="both your own user ('`whoami`') and for all users"
fi

echo
test "$(exec_input "Setup will remove the 'Xfce Evolution'-specific system tuning for $user_text, if any. Continue (y/N)?" y n)" != "y" && source ./lib/abort-common.sh
echo
if [ "$u" == "o" ]
then
  source ./lib/remove_qt_fix-common.sh "./lib/su-linux.sh" "user"
elif [ "$u" == "a" ]
then
  source ./lib/remove_qt_fix-common.sh "./lib/su-linux.sh" "system"
else # default
  source ./lib/remove_qt_fix-common.sh "./lib/su-linux.sh" "user" "system"
fi

if [ "$u" == "o" -a -d $themes_dir_system/'Xfce Evolution' ]
then
  echo "FYI"
  echo "---"
  echo "The 'Xfce Evolution'-specific system tuning has been removed for YOUR OWN USER."
  echo "If you'd like to also remove the 'Xfce Evolution'-specific system tuning for all users then you must run this uninstaller from the all-users themes folder '$themes_dir_system/Xfce Evolution/TOOLS/SETUP/'."
  echo
fi
if [ "$u" == "a" -a -d $themes_dir_user/'Xfce Evolution' ]
then
  echo "FYI"
  echo "---"
  echo "The 'Xfce Evolution'-specific system tuning has been removed for ALL USERS."
  echo "If you'd like to also remove the 'Xfce Evolution'-specific system tuning for your own user ('`whoami`') then you must run this uninstaller from your own users' themes folder '$themes_dir_user/Xfce Evolution/TOOLS/SETUP/'."
  echo
fi
source ./lib/done-common.sh
