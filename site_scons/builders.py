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
import shutil
import subprocess
import utils

def init(env):
    from SCons.Script import Builder
    bldRUT = Builder(action = SCons.Action.Action(RunUnittest, PrintDummy))
    env.Append(BUILDERS = {'RunUnittest' : bldRUT})
    bldDoxygen = Builder(action = SCons.Action.Action(RunDoxygen, PrintDummy))
    env.Append(BUILDERS = {'RunDoxygen' : bldDoxygen})
    env['DEFAULT_DOXYFILE'] = env.File('#/conf/doxygenTemplate').abspath

def PrintDummy(env, source, target):
    return ""

def RunUnittest(env, source, target):
    rc = 0
    t = target[0].abspath;
    for s in source:
        app = s.abspath
        (dir, appbin) = os.path.split(app)
        cmd = "cd %s; ./%s > %s" % (dir, appbin, t)
        rc = subprocess.call(cmd, shell=True)
        if env.GetOption('printresults'):
            subprocess.call("cat %s" % t, shell=True)
        if rc:
            env.cprint('[failed] %s, error: %s' % (t, rc), 'red')
        else:
            env.cprint('[passed] %s' % t, 'green')
    return rc

def RunDoxygen(target, source, env):
    (pathHead, pathTail) = os.path.split(source[0].abspath)
    fsrc = open(source[0].abspath, 'r')
    doxygenSrc = fsrc.read()
    fsrc.close()
    
    tmpdoxyFile = pathHead + '/tmp_doxyfile'
    targetName = os.path.basename(target[0].abspath)[:-4]
    
    ftgt = open(tmpdoxyFile, "w")
    ftgt.write(doxygenSrc.replace('$PROJECT_NAME', targetName)\
                         .replace('$OUTPUT_DIR', target[0].abspath))
    ftgt.flush()
    ftgt.close()
    subprocess.call('cd ' + pathHead + ' ; doxygen ' + tmpdoxyFile, shell=True)
    os.remove(tmpdoxyFile)

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

def RecursiveInstall(env, sourceDir, sourcesRel, targetName, fileFilter='*.*'):
    nodes = []
    if isinstance(sourcesRel, list or tuple):
        for source in sourcesRel:
            nodes.extend( utils.recursive_flatten(env, os.path.join(sourceDir,source), fileFilter ) )
    else:
        nodes.extend( utils.recursive_flatten(env, os.path.join(sourceDir,sourcesRel), fileFilter ) )
    l = len(sourceDir) + 1
    relnodes = [ n.abspath[l:] for n in nodes ]
    targetHeaderDir = env.Dir(env['INSTALL_HEADERS_DIR']).Dir(targetName).abspath
    targets = []
    sources = []
    for n in relnodes:
        t = env.File(os.path.join(targetHeaderDir, n))
        s = env.File(os.path.join(sourceDir, n))
        
        targets.append( t )
        sources.append( s )
    iAs = env.InstallAs(targets, sources)
    return iAs
