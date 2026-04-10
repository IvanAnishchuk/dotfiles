#!/bin/bash

su_cmd="$1"

echo "Removing Qt font fix..."
echo
echo "Removing QT_QPA_PLATFORMTHEME..."
echo
for user in "$2" "$3"
do
  test "$user" == "" && break

  source "$su_cmd" "$user"

  # remove qt5.7 font fix
  $sudo "rm -f $qt5_conf_dir/90-xfce-evolution_qt5fontfix.conf"

  # remove QT_QPA_PLATFORMTHEME from all supported shells' initialization files
  for sf in "${shell_init_files[@]}"
  do
    f=$(echo $sf | cut -d':' -f 2)
    #echo $f
    test -f $f && $sudo "$func_delines; exec_delines '#xfce-evolution' $f"
  done
done
