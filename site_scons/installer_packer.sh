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

# This is check_install implementation for Arch systems

function check_install {
    declare -A mappings
    mappings['make']='base-devel'
    mappings['moc']='qt'
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
        echo "info: 'sudo packer -S $pkg' should do the job, do you want"
        echo "      me to do it? (your password could be required)"
        REPLY="extremelyLongStringUnlikelyToBeUsed"
        while [[ "$REPLY" != "y" && "$REPLY" != "n" && "$REPLY" != "" ]]; do
            read -p "Install ([y]/n)?" REPLY
            if [[ "$REPLY" != "y" && "$REPLY" != "n" && "$REPLY" != "" ]]; then
                echo -e "\e[0;31mID-10-T Error: please insert 'y' or 'n' or nothing. \e[0m"
            fi
        done
        if [[ "$REPLY" = "y" || "$REPLY" = "" ]]; then
            sudo packer -S $pkg
            if [ "$?" -ne "0" ]; then
                echo -e "\e[0;31m[error] $1 (part of $pkg) could not be installed, exiting\e[0m"
                return 1
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
