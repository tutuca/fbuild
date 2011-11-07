#!/bin/sh
# Insert FuDePan boilerplate

# This file was written in shell scripting because we could not have python at this point
# After the first check that python is there, we jump to env.py to ensure we support as
# many platforms as we can. If another platform besides *nix is required, a different
# "shell env script" should be created.
# i.e. for windows a env.bat should be created.

if [ -z "${PYTHON_BIN_PATH+x}" ]; then
  export PYTHON_BIN_PATH=/usr/bin/python
fi

hg pull -u

sh init.sh

source system.sh

if [ -e library.sh ]; then
  source library.sh
fi
