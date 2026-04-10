#!/bin/bash

source ./lib/setenv-linux.sh
source ./lib/install_start-linux.sh
source ./lib/install_qtfix-common.sh
sudo bash -c "source ./lib/install_deps-linux-debian.sh; source ./lib/cleanup_legacy-linux.sh"
source ./lib/done-common.sh
