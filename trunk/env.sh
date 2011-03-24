#!/bin/sh
# Insert FuDePan boilerplate

# This file was written in shell scripting because we could not have python at this point
# After the first check that python is there, we jump to env.py to ensure we support as
# many platforms as we can. If another platform besides *nix is required, a different
# "shell env script" should be created.
# i.e. for windows a env.bat should be created.

# Check if python is installed
if [ ! "$(which python)" ]; then
    echo "warning: Python was not found, need to install python to continue"
    echo "info: 'sudo apt-get install python' should do the job, do you want"
    echo "      me to do it? (your password will be required)"
    read -p "Install (y/n)?" REPLY
    if [ "$REPLY" = "y" ]; then
        sudo apt-get install python
    else
        exit 1
    fi
fi

# Check if scons is installed
if [ ! "$(which scons)" ]; then
    echo "warning: scons was not found, need to install scons to continue"
    echo "info: 'sudo apt-get install scons' should do the job, do you want"
    echo "      me to do it? (your password will be required)"
    read -p "Install (y/n)?" REPLY
    if [ "$REPLY" = "y" ]; then
        sudo apt-get install scons
    else
        exit 1
    fi
fi

# jump to env.py
python env.py

