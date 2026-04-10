#!/bin/bash

test -z "$BASH_VERSION" && echo && echo "Shell 'bash' not found, you must install 'bash' to use this script." && read -s && exit
cd "$(dirname "${BASH_SOURCE[0]}")"

source ./lib/select_os-common.sh "The 'Xfce Evolution'-specific system tuning will be installed on your system."

if [ "$os" == "debian" ]
then
  source ./lib/install_helper-linux-debian.sh
elif [ "$os" == "ubuntu" ]
then
  source ./lib/install_helper-linux-ubuntu.sh
elif [ "$os" == "arch" ]
then
  source ./lib/install_helper-linux-arch.sh
elif [ "$os" == "fedora" ]
then
  source ./lib/install_helper-linux-fedora.sh
elif [ "$os" == "freebsd" ]
then
  source ./lib/install_helper-bsd-freebsd.sh
fi
