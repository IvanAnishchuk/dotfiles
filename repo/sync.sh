#!/bin/bash
set -e
for env in py2 py3; do
  cd $env
  pipenv install
  # skip these: 'pip2* pip3* pip python* wheel easy_install*'
  find \
    $(pipenv --venv)/bin \
    -type f -executable \
    -type l \
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
  find \
    $(pipenv --venv)/bin \
    -type l \
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
