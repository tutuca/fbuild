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


"""
    This file contains default configuration options for scons.
"""


import os.path
from multiprocessing import cpu_count

from SCons.Variables import PathVariable


INC_PATH_PREFIX = '-I'
LINK_PATH_PREFIX = '-L'
LINK_PREFIX = '-l'


def init(env, vars):
    # Add parallelism to the build system
    if not env.GetOption('num_jobs'):
        env.SetOption('num_jobs', cpu_count() + 1)
    # Some environment tunnings so this runs faster
    env.Decider('MD5-timestamp')
    env.SConsignFile()
    # Let the default to do nothing
    env.Default()
    # Get the scons root path, this can be tricky because
    # scons can be ran with the -v option
    INSTALL_DIR = os.path.join(env.Dir('#').abspath, "install")
    
    if env.GetOption('buildtests'):
        PROJECTS_DIR = env.Dir('#/buildtests').abspath
    else:
        PROJECTS_DIR = env.Dir('#/projects').abspath    
    vars.AddVariables(
        PathVariable(
            'WS_DIR',
            'workspace directory',
            PROJECTS_DIR,
            PathVariable.PathIsDirCreate)
        )
    vars.AddVariables(
        PathVariable(
            'BUILD_DIR',
            'build directory',
            os.path.join(env.Dir('#').abspath, "build"),
            PathVariable.PathIsDirCreate)
        )
    vars.AddVariables(
        PathVariable(
            'INSTALL_BIN_DIR',
            'install bin directory',
            os.path.join(INSTALL_DIR, "bin"),
            PathVariable.PathIsDirCreate)
        )
    vars.AddVariables(
        PathVariable(
            'INSTALL_HEADERS_DIR',
            'install headers directory',
            os.path.join(INSTALL_DIR, "includes"),
            PathVariable.PathIsDirCreate)
        )
    vars.AddVariables(
        PathVariable(
            'INSTALL_LIB_DIR',
            'install libs directory',
            os.path.join(INSTALL_DIR, "libs"),
            PathVariable.PathIsDirCreate)
        )
    vars.AddVariables(
        PathVariable(
            'INSTALL_DOC_DIR',
            'install docs directory',
            os.path.join(INSTALL_DIR, "docs"),
            PathVariable.PathIsDirCreate)
        )
    vars.AddVariables(
        PathVariable(
            'INSTALL_REPORTS_DIR',
            'software reports directory',
            os.path.join(INSTALL_DIR, "reports"),
            PathVariable.PathIsDirCreate)
        )
    vars.Update(env)
    REPORT_DIR = env.Dir(env['INSTALL_REPORTS_DIR']).abspath
    vars.AddVariables(
        PathVariable(
            'INSTALL_METRICS_DIR',
            'software metrics directory',
            os.path.join(REPORT_DIR, "metrics"),
            PathVariable.PathIsDirCreate)
        )
    env.SetDefault(
        CPPCHECK_SUPPRESSION = ''
        )
    vars.Update(env)
    if env.GetOption('verbose'):
        env.cdebug('Install information:')
        env.cdebug('    bin dir    : ' + env['INSTALL_BIN_DIR'])
        env.cdebug('    lib dir    : ' + env['INSTALL_LIB_DIR'])
        env.cdebug('    headers dir: ' + env['INSTALL_HEADERS_DIR'])
        env.cdebug('    doc dir    : ' + env['INSTALL_DOC_DIR'])
    ## Replace the scons _concat function for mine.
    replace_scons_concat_function(env)


def replace_scons_concat_function(env):
    old_concat = env['_concat']
    def new_concat(INCPREFIX, CPPPATH, INCSUFFIX, __env__, RDirs=None, *kwargs):
        if INCPREFIX == INC_PATH_PREFIX:
            result = old_concat(INCPREFIX, CPPPATH, INCSUFFIX, __env__, sorted, *kwargs)
        else:
            result = old_concat(INCPREFIX, CPPPATH, INCSUFFIX, __env__, lambda x : x, *kwargs)
        return result
    env['_concat'] = new_concat
