#!/bin/bash
#
# DEPRECATED: replaced by `tools-sync` (uv + npm) in phase B of the
# dotfiles modernization. Left as a reference for which tools the
# old pipenv-based installer was managing — `repo/py3/Pipfile` is
# the canonical list. This script is no longer wired up; the `py2`
# and `docker` envs were removed during phase A2 cleanup.
#
set -e
for env in py3; do
  cd $env
  pipenv install
  # skip these: 'pip2* pip3* pip python* wheel easy_install*'
  find \
    $(pipenv --venv)/bin \
    \( \( -type f -executable \) -o -type l \) \
    -not \( \
      -name python -o -name 'python[0-9]*' -o \
      -name python-config -o -name 'python-config[0-9]*' -o \
      -name pip -o -name 'pip[0-9]*' -o \
      -name easy_install -o -name 'easy_install-[0-9]*' -o \
      -name wheel \
    \) \
    -print0 \
    | while IFS= read -r -d '' file
  do
    cp -v $file ~/.local/bin
  done
  cd ..
done
