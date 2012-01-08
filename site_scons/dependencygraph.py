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

#
# Description: this file contains a graph with dependencies between the
#              components to better solve include paths and library linking
#
import fnmatch
import os
from SCons.Script.SConscript import SConsEnvironment

isPreProcessing = False
downloadedDependencies = False

def init(env):
    SConsEnvironment.CreateProgram = CreateProgram
    SConsEnvironment.CreateStaticLibrary = CreateStaticLibrary
    SConsEnvironment.CreateSharedLibrary = CreateSharedLibrary
    SConsEnvironment.CreateHeaderOnlyLibrary = CreateHeaderOnlyLibrary
    SConsEnvironment.CreateTest = CreateTest
    #SConsEnvironment.CreateAutoToolsProject = CreateAutoToolsProject
    # AddComponent is a workaround that we should never require to use
    # we leave this just for temporary solutions but if this is enabled, there
    # is something to do
    #env.AddComponent = AddComponent
    SConsEnvironment.CreateDoc = CreateDoc

class ComponentDictionary:
    components = {}
    
    def add(self, env, component):
        if not component.name.lower() == component.name:
            env.cprint('[warn] modules names should be lower case: ' + name, 'yellow')
        # Its possible that a component is tried to be added twice because a new
        # dependency was downloaded and 
        if not self.components.has_key(component.name):
            self.components[component.name] = component
        else:
            print 'Component trying to be re-added: ' + component.name
    
    def get(self, name):
        if self.components.has_key(name):
            return self.components[name]
        else:
            return None

componentGraph = ComponentDictionary()
allComponents = []

class Component(object):
    def __init__(self, name, type, inc = [], deps = [], extInc = None):
        self.name = name
        self.type = type
        self.inc = inc
        self.extInc = extInc
        self.deps = deps
        allComponents.append(name)

    class Type:
        HEADER_ONLY = 0
        PROGRAM = 1
        UNITTEST = 2
        STATIC_LIBRARY = 3
        SHARED_LIBRARY = 4
        DOC = 5

    def GetDependenciesPaths(self, env):
        (depLibPaths, depLibs, depIncs) = self.getPaths(env)
        depLibPaths.append(env['INSTALL_LIB_DIR'])
        depIncs.append(env['INSTALL_HEADERS_DIR'])
        return (depIncs, depLibs, depLibPaths)

    def getPaths(self, env):
        libpaths = []
        libs = []
        incs = []
        # First, add the stuff of this library so this goes first than the
        # dependencies
        incs.append(self.inc)
        
        # Second step, get the paths from the dependencies. 
        # TODO: We need a way to check for circular dependencies 
        #       since this algorithm can hang
        for dep in self.deps:
            c = componentGraph.get(dep)
            if c is None:
                env.cprint('[error] %s depends on %s which could not be found' % (self.name, dep), 'red')
                continue
            (depIncs, depLibs, depLibPaths) = c.getPaths(env)
            libpaths.extend(depLibPaths)
            libs.extend(depLibs)
            incs.extend(depIncs)
            if c.type in [Component.Type.STATIC_LIBRARY, 
                          Component.Type.SHARED_LIBRARY]:
                libs.append(c.name)
                libDir = os.path.join(env['BUILD_DIR'], c.name)
                libpaths.append(libDir)
            if c.type in [Component.Type.STATIC_LIBRARY, 
                          Component.Type.SHARED_LIBRARY,
                          Component.Type.HEADER_ONLY]:
                hDir = os.path.join(env['INSTALL_HEADERS_DIR'], c.name)
                incs.append(hDir)
        return (incs, libs, libpaths)

def CreateHeaderOnlyLibrary(env, name, inc, ext_inc, deps):
    if isPreProcessing:
        componentGraph.add(env, Component(name,
                                          Component.Type.HEADER_ONLY,
                                          inc,
                                          deps,
                                          ext_inc
                                          ))
    else:
        hLib = env.HeaderLibrary(ext_inc, ext_inc)
        iHLib = env.Install(env['INSTALL_HEADERS_DIR'], hLib)
        env.Alias(name, iHLib, 'Install ' + name + ' headers')
        env.Alias('all:install', iHLib, "Install all targets")

def CreateProgram(env, name, inc, src, deps):
    if isPreProcessing:
        componentGraph.add(env, Component(name,
                                          Component.Type.PROGRAM,
                                          inc,
                                          deps))
    else:
        (incpaths,libpaths,libs) = componentGraph.get(name).GetDependenciesPaths(env)
        prog = env.Program(name, src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        # TODO: extend this to other types
        env.Alias('all:build', prog, "Build all targets")
        iProg = env.Install(env['INSTALL_BIN_DIR'], prog)
        env.Alias(name, iProg, "Build and install " + name)
        env.Alias('all:install', iProg, "Install all targets")
    
def CreateTest(env, name, inc, src, deps):
    testName = name + ':test'
    if isPreProcessing:
        componentGraph.add(env, Component(testName,
                                          Component.Type.UNITTEST,
                                          inc,
                                          deps))
    else:
        (incpaths,libpaths,libs) = componentGraph.get(testName).GetDependenciesPaths(env)
        tProg = env.Program(testName, src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        # TODO: add reference folders
        env.Alias('all:build', tProg, "Build all targets")
        tTest = env.RunUnittest(testName + '.passed', tProg)
        env.Alias(testName, tTest, "Run test for " + name)
        env.Alias('all:test', tTest, "Run all tests")
    
def CreateStaticLibrary(env, name, inc, ext_inc, src, deps):
    if isPreProcessing:
        componentGraph.add(env, Component(name,
                                          Component.Type.STATIC_LIBRARY,
                                          inc,
                                          deps))
    else:
        (incpaths,libpaths,libs) = componentGraph.get(name).GetDependenciesPaths(env)
        # TODO: Is this the correct way to handle it? to create a header only
        # library and to install it when its built? 
        #hLib = env.HeaderLibrary(name, ext_inc)
        #iHLib = env.Install(env['INSTALL_HEADERS_DIR'], hLib)
        #env.Alias(name, hLib, "Build " + name)
        sLib = env.Library(name, src, CPPPATH=incpaths)
        env.Alias(name, sLib, "Build " + name)
        env.Alias('all:build', sLib, "install all targets")
    
def CreateSharedLibrary(env, name, inc, ext_inc, src, deps):
    if isPreProcessing:
        componentGraph.add(env, Component(name,
                                          Component.Type.SHARED_LIBRARY,
                                          inc,
                                          deps))
    else:
        (incpaths,libpaths,libs) = componentGraph.get(name).GetDependenciesPaths(env)
        # TODO: Is this the correct way to handle it? to create a header only
        # library and to install it when its built? 
        #hLib = env.HeaderLibrary(name, ext_inc)
        #iHLib = env.Install(env['INSTALL_HEADERS_DIR'], hLib)
        #env.Alias(name, hLib, "Build " + name)
        dLib = env.SharedLibrary(name, src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        iLib = env.Install(env['INSTALL_BIN_DIR'], dLib)
        env.Alias(name, iLib, "Build and install " + name)
        env.Alias('all:build', sLib, "install all targets")
    
#def CreateAutoToolsProject(env, name, libfile, configureFile, ext_inc):
#    if isPreProcessing:
#        componentGraph.add(env, Component(name))
    
def CreateDoc(env, name, doxyfile=None):
    if isPreProcessing:
        componentGraph.add(env, Component(name,
                                          Component.Type.DOC))

def WalkDirsForSconscripts(env, topdir, ignore = []):
    global isPreProcessing
    global downloadDependencies
    global allComponents
    
    isPreProcessing = True
    # Step 1: load all the components in the dependency graph
    # if we find a download dependency, we download it and re-process everything
    # to be sure that all the components are downloaded and loaded in the
    # dependency graph
    # Initial set to pass the loop test
    downloadedDependencies = True
    while downloadedDependencies:
        downloadedDependencies = False
        for root, dirnames, filenames in os.walk(topdir):
            if ignore.count(os.path.relpath(root, topdir)) == 0:
                for filename in fnmatch.filter(filenames, 'SConscript'):
                    pathname = os.path.join(root, filename)
                    env.SConscript(pathname, exports='env')
        # Check if there is a component that we dont know how to build
        for component in allComponents:
            if componentGraph.get(component) == None:
                # check if we know how to download this component
                downloadedDependencies = True
        if downloadedDependencies:
            allComponents = []
        #TODO small hack while we dont have the downloading
        downloadedDependencies = False
        
    # Step 2: real processing we have everything loaded in the dependency graph
    # now we process it
    isPreProcessing = False
    for root, dirnames, filenames in os.walk(topdir):
        if ignore.count(os.path.relpath(root, topdir)) == 0:
            for filename in fnmatch.filter(filenames, 'SConscript'):
                pathname = os.path.join(root, filename)
                env.SConscript(pathname, exports='env')