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

from SCons.Script.SConscript import SConsEnvironment
from SCons.Script import *
import SCons.Builder

def init(env):
    from SCons.Script import Builder
    bldHL = Builder(action = SCons.Action.Action(HeaderLibrary, PrintDummy))
    env.Append(BUILDERS = {'HeaderLibrary': bldHL})
    bldRUT = Builder(action = SCons.Action.Action(RunUnittest, PrintDummy))
    env.Append(BUILDERS = {'RunUnittest' : bldRUT})
    
def PrintDummy(env, source, target):
    return ""

def HeaderLibrary(env, source, target):
    # Copy headers
    return;
    #if not self.processed and self.externalHeaderDirs:
    #for d in self.externalHeaderDirs:
    #    for f in os.listdir(d):
    #        if not f.startswith('.'):
    #            path = os.path.join(d, f)
    #            if os.path.isdir(path):
    #                recursive_install.RecursiveInstall(env, self.installIncludesDir, path)
    #            else:
    #                t = env.Install(self.installIncludesDir, path)
    #                env.jAlias('all:install', t, "install all targets")
    #self.processed = True #TODO: gtest_main.abspath()

def RunUnittest(env, source, target):
    for s in source:
        app = str(s.abspath)
        (dir, appbin) = os.path.split(app)
        rc = subprocess.call("cd %s; ./%s" % (dir, appbin), shell=True)
        if rc:
            cprint('[error] %s failed, error: ' % (app, rc), 'red')
        else:
            cprint('[passed] %s passed' % app, 'green')

#def configure(target, source, env):
#    buildDir = env['buildDir']
#    configure = env['configurePath']
#    configureOpts = (' --bindir=%(INSTALL_BIN_DIR)s --libdir=%(INSTALL_LIB_DIR)s --includedir=%(INSTALL_HEADERS_DIR)s' % env)
#    procEnv = os.environ
#    (arch,binType) = platform.architecture()
#    if arch == '64bit':
#        procEnv["CXXFLAGS"] = str(env["CXXFLAGS"])
#        procEnv["CFLAGS"] = '-fPIC'
#
#    return subprocess.call(configure + configureOpts + ' ; make; make install', cwd=buildDir, shell=True, env=procEnv)

