#!/bin/bash

source ./lib/setenv-common.sh

function exec_delines() {
  local x
# a=`whoami`
# echo $a
  x="sed -i '' '/$1/d' '$2'"
# echo $x
  eval $x
}
func_delines=`declare -f exec_delines`

themes_dir_system="/usr/local/share/themes"
themes_dir_user="$HOME/.themes"
qt5_conf_dir_system="/usr/local/etc/fonts/conf.d"
qt5_conf_dir_user="$HOME/.config/fontconfig/conf.d"
if [ "$(exec_issystem)" ]
then
  qt5_conf_dir=$qt5_conf_dir_system
  themes_dir=$themes_dir_system
else
  qt5_conf_dir=$qt5_conf_dir_user
  themes_dir=$themes_dir_user
fi
