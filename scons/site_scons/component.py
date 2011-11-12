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

# FuDePan boilerplate required here

import fnmatch
import os
import SCons
from dependencies import downloadDependency
from dependencies import findLoadableDependencies

isPreProcessing = False
SConscriptFiles = {}
components = {}
downloadableDependencies = []

def GetDependenciesPaths(compName, env, deps):
    def search(deps):
        libpaths = []
        libs = []
        incs = []
        for dep in deps:
            comp = _findComponent(dep)
            if comp.external:
                incs += comp.headerDirs
            if comp.type == 'static_lib':
                libpaths.append(comp.buildDir)
            if comp.type in ["static_lib", "shared_lib", 'lib', 'autotools']:
                libs.append(dep)
            (recursiveLibPathReturn, recursiveLibReturn, recursiveIncs) = search(comp.deps)
            libpaths.extend(recursiveLibPathReturn)
            libs.extend(recursiveLibReturn)
            incs.extend(recursiveIncs)
        return (libpaths, libs, incs)
    comp = _findComponent(compName)
    libpaths, libs, incs = search(deps)
    incpaths = incs + [env['INSTALL_HEADERS_DIR']] + _buildPathList(comp.headerDirs, lambda d: d.abspath)
    libpaths.append(env['INSTALL_LIB_DIR'])
    return (incpaths, libpaths, libs)

# takes an string or a to_path function parameter, or a list.
def _buildPathList(headerDirs, to_path):
    _as_path = lambda _dir: _dir if isinstance(_dir, str) else to_path(_dir)

    if isinstance(headerDirs, list) or isinstance(headerDirs, tuple):
        return [_as_path(_dir) for _dir in headerDirs]
    else:
        return [_as_path(headerDirs)]

class Component(object):
    def __init__(self, name, headerDirs, deps, buildDir, installIncludesDir, externalHeaderDirs, type):
        self.name = name
        self.headerDirs = _buildPathList(headerDirs, lambda d: d.abspath)
        self.externalHeaderDirs = _buildPathList(externalHeaderDirs, lambda d: d.abspath) if externalHeaderDirs else None
        self.buildDir = buildDir
        self.installIncludesDir = installIncludesDir
        self.deps = deps
        self.sconscriptPath = None
        self.processed = False
        self.type = type
        self.external = False

    def copyHeaders(self, env):
        if not self.processed and self.externalHeaderDirs:
            for d in self.externalHeaderDirs:
                for f in os.listdir(d):
                    if not f.startswith('.'):
                        path = os.path.join(d, f)
                        if os.path.isdir(path):
                            env.RecursiveInstall(self.installIncludesDir, path)
                        else:
                            t = env.Install(self.installIncludesDir, path)
                            env.Alias('install', t)
            self.processed = True #TODO: gtest_main

def setupComponent(env, type, name, inc, deps, externalHeaderDirs=None):
    buildDir = os.path.join(env['BUILD_DIR'], name)
    installIncludesDir = os.path.join(env['INSTALL_HEADERS_DIR'], name)
    return Component(name, inc, deps, buildDir, installIncludesDir, externalHeaderDirs, type)

# it has deps because it can pull other libraries
def CreateHeaderOnlyLibrary(env, name, inc, ext_inc, deps):
    if isPreProcessing:
        _addComponent(env, name, setupComponent(env, 'header_only', name, inc, deps, ext_inc))
    else:
        _findComponent(name).copyHeaders(env)

def CreateProgram(env, name, inc, src, deps):
    if isPreProcessing:
        _addComponent(env, name, setupComponent(env, 'program', name, inc, deps))
    else:
        (incpaths,libpaths,libs) = GetDependenciesPaths(name, env, deps)
        progEnv = env.Clone()
        program = progEnv.Program(name, src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        progEnv.Alias('build_all', program)
        install = progEnv.Install(env['INSTALL_BIN_DIR'], program)
        progEnv.Alias(name, install)
        progEnv.Alias('install', install)

def CreateTest(env, name, inc, src, deps):
    if isPreProcessing:
        name = name + ':test'
        _addComponent(env, name, setupComponent(env, 'test', name, inc, deps))
    else:
        (incpaths,libpaths,libs) = GetDependenciesPaths(name, env, deps)
        libEnv = env.Clone()
        testEnv = env.Clone()
        component = _findComponent(name)
        if not component:
            raise Exception('The unit test is trying to test component %s which does not exists' % name)
        else:            
            buildDir = component.buildDir
            testEnv.PrependENVPath('LD_LIBRARY_PATH', buildDir)
            testEnv.Append(RPATH = ':' + buildDir)
            for p in libpaths: 
                testEnv.PrependENVPath('LD_LIBRARY_PATH', p)
                testEnv.Append(RPATH = ':' + p)
            name = name + ':test'
            test = testEnv.Program(name, src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
            testEnv.Alias('build_all', test)
            runtest = testEnv.Test(name + '.passed', test)
            testEnv.Alias(name, runtest)
            testEnv.Alias('run_all', runtest)
        
def CreateStaticLibrary(env, name, inc, ext_inc, src, deps):
    if isPreProcessing:
        _addComponent(env, name, setupComponent(env, 'static_lib', name, inc, deps, ext_inc))
    else:
        (incpaths,libpaths,libs) = GetDependenciesPaths(name, env, deps)
        libEnv = env.Clone()
        _findComponent(name).copyHeaders(libEnv)
        compLib = libEnv.Library(name, src, CPPPATH=incpaths)
        libEnv.Alias(name, compLib)
        libEnv.Alias('build_all', compLib)

# For static libraries we will make a version header only
# of the lib so a component can depend on this one in a light way
def CreateSharedLibrary(env, name, inc, ext_inc, src, deps):
    if isPreProcessing:
        _addComponent(env, name, setupComponent(env, 'shared_lib', name, inc, deps, ext_inc))
    else:
        (incpaths,libpaths,libs) = GetDependenciesPaths(name, env, deps)
        dlibEnv = env.Clone()
        _findComponent(name).copyHeaders(dlibEnv)
        dlib = dlibEnv.SharedLibrary(name, src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        install = dlibEnv.Install(env['INSTALL_LIB_DIR'], dlib)
        dlibEnv.Alias(name, install)
        dlibEnv.Alias('build_all', dlib)
        dlibEnv.Alias('install', install)

def CreateAutoToolsProject(env, name, libfile, configureFile, ext_inc):
    if isPreProcessing:
        _addComponent(env, name, setupComponent(env, 'autotools', name, [], [], []))
    else:
        component = _findComponent(name)
        buildDir = component.buildDir
        libEnv = env.Clone()
        target = [ os.path.join(env['INSTALL_LIB_DIR'], libfile) ]
        target += [os.path.join(component.installIncludesDir, f.name) for f in ext_inc]
        if not os.path.exists(buildDir):
            os.makedirs(buildDir)
        c = libEnv.Configure(target, 'configure', buildDir=buildDir, configurePath=configureFile.abspath)
        libEnv.Alias(name, c)
        libEnv.Alias('build_all', c)
        libEnv.Alias('install', c)

def AddComponent(env, name, headerDirs, deps, buildDir = '', isLib = False):
    global components
    component = Component(name, headerDirs, deps, buildDir, '', None, 'lib' if isLib else 'component')
    component.processed = True
    component.external = True
    components[name] = component

#Just load all components.
def WalkDirsForComponents(env, topdir, ignore):
    # Step 1: populate all the components
    for root, dirnames, filenames in os.walk(topdir):
        if ignore.count(os.path.relpath(root, env.Dir('#').abspath)) == 0:
            for filename in fnmatch.filter(filenames, 'SConscript'):
                pathname = os.path.join(root, filename)
                _pre_process_component(env, pathname)

def initializeDependencies(env):
    global downloadableDependencies 
    confDir = env.Dir('#/../conf/').abspath
    downloadableDependencies = findLoadableDependencies(env, confDir)

def process(env, target):
    global components
    global downloadableDependencies
	
    component = _findComponent(target)
    if component:
        for dep in component.deps:
            if not components.has_key(dep):
                downloadableDependency = downloadableDependencies.get(dep)
                denv = env.Clone()
                denv['EXTERNAL_DIR'] = env.Dir('#/site_scons/external').abspath
                denv['ROOT'] = env.Dir('#').abspath
                if downloadDependency(downloadableDependency, denv):
                    pathname = os.path.join(downloadableDependency.target, "SConscript")
                    if not os.path.exists(pathname):
                        raise Exception('Could not found SConscript for: %s' % dep)
                    else:
                        _pre_process_component(env, pathname)
                else:
                    raise Exception('Could not found dependency: %s' % dep)
            process(env, dep)
        _process_component(env, component)
    else:
        raise Exception('Could not found target: %s' % target)

def _pre_process_component(_env, sconscriptPath):
    global isPreProcessing
    isPreProcessing = True
    env = _env.Clone()
    env.SConscript(sconscriptPath, exports='env')
    isPreProcessing = False

def _process_component(_env, component):
    if component.sconscriptPath and not component.processed:
        env = _env.Clone()
        if component.type == 'test':
            env.SConscript(component.sconscriptPath, variant_dir=component.buildDir, duplicate=0, exports='env', src_dir='..')
        else:
            env.SConscript(component.sconscriptPath, variant_dir=component.buildDir, duplicate=0, exports='env')
        component.processed = True

#TODO: rename?
def _addComponent(env, name, component):
    global components
    component.sconscriptPath = os.path.join(env.Dir('.').abspath, "SConscript")
    component.projectDir = env.Dir('.').abspath
    components[name] = component

def _findComponent(name):
    return components.get(name)
