#!/bin/bash

source ./lib/setenv-bsd-freebsd.sh
source ./lib/install_start-bsd-freebsd.sh
source ./lib/install_qtfix-common.sh
su -m root -c bash -c "source ./lib/install_deps-bsd-freebsd.sh; source ./lib/cleanup_legacy-bsd-freebsd.sh"
source ./lib/done-common.sh
