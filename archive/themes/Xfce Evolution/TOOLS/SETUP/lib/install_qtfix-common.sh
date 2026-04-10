#!/bin/bash

# install qt5.7+ font fix
echo "Installing Qt font fix..."
echo
$sudo "mkdir -p $qt5_conf_dir"
$sudo "rm -f $qt5_conf_dir/90-xfce-evolution_qt5fontfix.conf" # MUST explicitly remove if exists
$sudo "cp $themes_dir/'Xfce Evolution'/90-xfce-evolution_qt5fontfix.conf $qt5_conf_dir" # used to be "cp --no-preserve=all ...", but that's not working on freebsd, and it's not needed in this version

# set QT_QPA_PLATFORMTHEME in all supported shells' initialization files
echo "Installing QT_QPA_PLATFORMTHEME..."
echo
for sf in "${shell_init_files[@]}"
do
  s=$(echo $sf | cut -d':' -f 1)
  f=$(echo $sf | cut -d':' -f 2)
# echo $s $f
  if [ -f $f ]
  then
    [ "$(tail -c 1 "$f" | wc -l)" -eq 0 ] && $sudo "echo >> $f"
    $sudo "$func_delines; exec_delines '#xfce-evolution' $f"
    if [ "$s" == "csh" ]
    then
      set_qt_theme="setenv QT_QPA_PLATFORMTHEME gtk2"
    else
      set_qt_theme="export QT_QPA_PLATFORMTHEME=gtk2"
    fi
    set_qt_theme=$set_qt_theme" #xfce-evolution_qt5-gtk2" # xfce-evolution marker for uninstall
    $sudo "echo '$set_qt_theme' >> $f"
#   $sudo "echo '[ \"\$(which xfconf-query | grep \"/\")\" -a \"\$(xfconf-query -c xsettings -p /Net/ThemeName | grep -i \"xfce evolution \")\" ] && $set_qt_theme' >> $f"
#   $sudo "echo '[ ! \"\$(which xfconf-query | grep \"/\")\" ] && $set_qt_theme' >> $f"
  fi
done
