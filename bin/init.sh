#!/bin/bash

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

# This file was written in shell scripting because we could not have python at this point
# After the first check that python is there, we jump to env.py to ensure we support as
# many platforms as we can. If another platform besides *nix is required, a different
# "shell env script" should be created.
# i.e. for windows a env.bat should be created.

function ubuntuInstall {
    UBUNTU=`cat /etc/issue | grep Ubuntu`
    if [ -n "$UBUNTU" ]; then
      echo "info: 'sudo apt-get install $1' should do the job, do you want"
      echo "      me to do it? (your password will be required)"
      read -p "Install (y/n)?" REPLY
      if [ "$REPLY" = "y" ]; then
          sudo apt-get install $1
      else
          if [ "$2" = 'required' ]; then
            exit 1
          fi
      fi
    fi
}

# Check if the build-essential tools are installed
if [ ! "$(which g++)" ]; then
    echo "error: Essential development tools were not found, need to install them to continue"
    ubuntuInstall build-essential 'required'
fi

# Check if python is installed
if [ ! "$(which python)" ]; then
    echo "error: Python was not found, need to install python to continue"
    ubuntuInstall python 'required'
fi

# Check if scons is installed
if [ ! "$(which scons)" ]; then
    echo "error: scons was not found, need to install scons to continue"
    ubuntuInstall scons 'required'
fi

# Check if qt is installed (we use the moc executable)
if [ ! "$(which moc)" ]; then
    echo "warning: qt was not found, qt is not required to continue"
    ubuntuInstall qt4-dev-tools
fi

if [ ! "$(which doxygen)" ]; then
    echo "warning: doxygen was not found, doxygen is not required to continue"
    ubuntuInstall doxygen 
fi

# Check if python config module is installed
$PYTHON_BIN_PATH -m config 2> /dev/null
if [ $? -ne 0 ]; then
    echo "error: python config module not found, need to install config module to continue"
    read -p "Install (y/n)?" REPLY
    if [ "$REPLY" = "y" ]; then
      wget http://www.red-dove.com/config-0.3.9.tar.gz && 
        tar zxvf config-0.3.9.tar.gz && cd config-0.3.9 && sudo python setup.py install &&
          cd .. && sudo rm -rf config-0.3.9*
    else
        exit 1
    fi
fi

$PYTHON_BIN_PATH -m argparse 2> /dev/null
if [ $? -ne 0 ]; then
    echo "error: python argparse module not found, need to install it to continue"
    ubuntuInstall python-argparse 'required'
fi

# jump to env.py
$PYTHON_BIN_PATH bin/env.py

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$PWD/install/libs
