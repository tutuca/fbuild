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

#import os
#import platform
#import sys
import SCons

env = Environment()
Export('env')

vars = Variables('SConfig')
Export('vars')

# default configuration options
import scons_defaults
scons_defaults.init(env,vars)

# Color pretty printing
import termcolor
termcolor.init(env, ARGUMENTS)

# things to debug the environment
import debug
debug.init(env)

# Imports compiler stuff
import compiler
compiler.init(env)

# Linker options
import linker
linker.init(env)

# Include the aliases helper
import helpfromaliases
helpfromaliases.init(env)

# Include the builders
import builders
builders.init(env)

# Include the graph dependency solver
import dependencygraph
dependencygraph.init(env)

# Include the dependencies checkout and update system
import dependencies
dependencies.init(env)

# Add OS Components
import linux
linux.init(env)

#
## Register builders
## Register tools
#env.Tool('makebuilder')
#
## Create a builder for tests
#import builders
#bld = Builder(action = builders.runTest)
#configure = Builder(action = builders.configure)
#env.Append(BUILDERS = {'Test':  bld, 'Configure': configure})
#
## Create a builder for doxygen
#import doxygen
#doxygenBuilder = Builder(action = doxygen.runDoxygen)
#env.Append(BUILDERS = {'Doxygen':  doxygenBuilder})
#env['DEFAULT_DOXYFILE'] = env.File('#/conf/doxygenTemplate').abspath
#
## Add Qt
#import qtutil
#qtutil.preDetectQt(env)
#qtutil.addQtComponents(env)
#import boostutil
#boostutil.addBoostComponents(env)
#
#
#
## call to fudepan.py where
#import fudepan
#fudepan.setDefines(env)
#
#env.cprint('Install information:', 'green')
#env.cprint('    bin dir    : ' + env['INSTALL_BIN_DIR'], 'green')
#env.cprint('    lib dir    : ' + env['INSTALL_LIB_DIR'], 'green')
#env.cprint('    headers dir: ' + env['INSTALL_HEADERS_DIR'], 'green')
#
## Walk over the tree finding components
#from component import WalkDirsForComponents
dependencygraph.WalkDirsForSconscripts(env, topdir = env['WS_DIR'],
                                       ignore = [
                                                 'gmock/scons',
                                                 'test_doc',
                                                 'test_program',
                                                 'test_qt',
                                                 'test_shared',
                                                 'test_static',
                                                 'test_ut'
                                                ])

#component.initializeDependencies(env)
#
#for target in list(component.components): #make a copy
#    component.process(env, target)

