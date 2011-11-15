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

function fudepan-install {
    sudo $PYTHON_BIN_PATH bin/fbuild.py INSTALL_HEADERS_DIR=/usr/local/include/ INSTALL_BIN_DIR=/usr/local/bin/ INSTALL_LIB_DIR=/usr/local/lib/ $* install
}

_fbuild() {
    cur="${COMP_WORDS[COMP_CWORD]}"
    if [ -z $cur ]; then
        COMPREPLY=(`ls projects`)
    else
        TMP=`find projects/$cur* -maxdepth 0 2> /dev/null`
        if [ $? = "0" ]; then
          COMPREPLY=(`find projects/$cur* -maxdepth 0 | cut -f2 -d'/'`)
        fi
    fi
}
complete -F _fbuild -o nospace fbuild
