#!/bin/bash

test -z "$BASH_VERSION" && echo && echo "Shell 'bash' not found, you must install 'bash' to use this script." && read -s && exit
cd "$(dirname "${BASH_SOURCE[0]}")"

source ./lib/select_os-common.sh "The 'Xfce Evolution'-specific system tuning will be removed from your system."

if [ "$os" == "debian" ]
then
  source ./lib/uninstall_helper-linux.sh
elif [ "$os" == "ubuntu" ]
then
  source ./lib/uninstall_helper-linux.sh
elif [ "$os" == "arch" ]
then
  source ./lib/uninstall_helper-linux.sh
elif [ "$os" == "fedora" ]
then
  source ./lib/uninstall_helper-linux.sh
elif [ "$os" == "freebsd" ]
then
  source ./lib/uninstall_helper-bsd-freebsd.sh
fi
