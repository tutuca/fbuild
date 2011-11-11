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

# FuDePan boilerplate requierd here

import os
import sys

BUILD_SCRIPTS_DIR = os.path.join(os.getcwd(), "scons/site_scons")
sys.path.append(BUILD_SCRIPTS_DIR)

# Get the QT Directory
QTDIR = os.environ.get('QTDIR',None)
if not QTDIR:
    os.putenv('QTDIR','/usr')

# Welcome message    
from termcolor import cprint
cprint('Welcome to the FuDePAN console environment','green')
