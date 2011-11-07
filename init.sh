#!/bin/sh

# fudepan-build: The build system for FuDePAN projects 
#
# Copyright (C) 2011 Esteban Papp, Hugo Arregui FuDePAN
# 
# This file is part of the fudepan-build build system.
# 
# fudepan-build is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# fudepan-build is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with fudepan-build.  If not, see <http://www.gnu.org/licenses/>.

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

# Check if scons is installed
if [ ! "$(which moc)" ]; then
    echo "warning: qt was not found, qt is not required to continue"
    echo "info: 'sudo apt-get install qt4-dev-tools' should do the job, do you want"
    echo "      me to do it? (your password will be required)"
    read -p "Install (y/n)?" REPLY
    if [ "$REPLY" = "y" ]; then
        sudo apt-get install qt4-dev-tools
    else
        exit 1
    fi
fi

# Check if python config module is installed
$PYTHON_BIN_PATH -m config 2> /dev/null
if [ $? -ne 0 ]; then
    echo "warning: python config module not found, need to install config module to continue"
    read -p "Install (y/n)?" REPLY
    if [ "$REPLY" = "y" ]; then
      wget http://www.red-dove.com/config-0.3.9.tar.gz && 
        tar zxvf config-0.3.9.tar.gz && cd config-0.3.9 && sudo python setup.py install &&
          cd .. && sudo rm -rf config-0.3.9*
    else
        exit 1
    fi
fi

# jump to env.py
$PYTHON_BIN_PATH env.py

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$PWD/install/libs
