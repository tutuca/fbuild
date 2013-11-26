#!/bin/bash

# fudepan-build: The build system for FuDePAN projects 
#
# Copyright (C) 2011-2012 Esteban Papp, Hugo Arregui,
#               2013 Gonzalo Bonigo, Gustavo Ojeda, Matias Iturburu,
#                    Leandro Moreno, FuDePAN
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

# This is check_install implementation for Debian/Ubuntu systems

if [ -f /etc/lsb-release ]; then
    source /etc/lsb-release
    OS=$DISTRIB_ID
    VER=$DISTRIB_RELEASE
elif [ -f /etc/debian_version ]; then
    OS=Debian  # XXX or Ubuntu??
    VER=$(cat /etc/debian_version);
fi

function check_install {
    declare -A mappings
    mappings['make']='build-essential'
    mappings['moc']='qt4-dev-tools'
    mappings['dot']='graphviz'
    mappings['svn']='subversion'

    pkg=${mappings[$1]}
    if [ -z $pkg ]; then
        pkg=$1
    fi

    if [ ! "$(which $1)" ]; then
        if [ "$2" = "true" ]; then
            echo -e "\e[0;31m[error] $1 (part of $pkg) not found, need to install it to continue\e[0m"
        else
            echo -e "\e[0;33m[warn] $1 (part of $pkg) not found, suggest to install it to continue\e[0m"
        fi
        echo "info: 'I can try installing $pkg for you shall I proceed? (your password could be required)"
        REPLY="extremelyLongStringUnlikelyToBeUsed"
        while [[ "$REPLY" != "y" && "$REPLY" != "n" && "$REPLY" != "" ]]; do
            read -p "Install ([y]/n)?" REPLY
            if [[ "$REPLY" != "y" && "$REPLY" != "n" && "$REPLY" != "" ]]; then
                echo -e "\e[0;31mID-10-T Error: please insert 'y' or 'n' or nothing. \e[0m"
            fi
        done
        if [[ "$REPLY" = "y" || "$REPLY" = "" ]]; then
            # Check if pkg is clang, a different behave is necessary here.
            if [ "$pkg" == "clang" ]; then
                # Ubuntu 13.04 has clang with Address Sanitizer.
                if [ "$VER" == "13.04" ]; then
                    sudo apt-get install $pkg
                elif [ "$VER" == "12.04" ]; then
                    echo -e "Installing clang version 3.4"
                    if [ -z `grep llvm -R /etc/apt/sources.list*` ]; then
                        echo 'deb http://llvm.org/apt/precise/ llvm-toolchain-precise main' | sudo tee -a /etc/apt/sources.list.d/llvm.list
                    fi
                    wget -O - http://llvm.org/apt/llvm-snapshot.gpg.key|sudo apt-key add -
                    sudo apt-get update && sudo apt-get -y install clang-3.4
                fi
            else
                sudo apt-get install $pkg
                if [ "$?" -ne "0" ]; then
                    echo -e "\e[0;31m[error] $1 (part of $pkg) could not be installed, exiting\e[0m"
                    return 1
                fi
            fi
        else
            if [ "$2" = "true" ]; then
                echo -e "\e[0;31m[error] $1 (part of $pkg) required, exiting\e[0m"
                return 1
            fi
        fi
    fi
    unset mappings
    return 0
}
