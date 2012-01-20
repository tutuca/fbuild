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
from builders import RecursiveInstall

isPreProcessing = True
downloadedDependencies = False

headersFilter = ['*.h','*.hpp']

def init(env):
    from SCons.Script.SConscript import SConsEnvironment
    SConsEnvironment.CreateProgram = CreateProgram
    SConsEnvironment.CreateStaticLibrary = CreateStaticLibrary
    SConsEnvironment.CreateSharedLibrary = CreateSharedLibrary
    SConsEnvironment.CreateHeaderOnlyLibrary = CreateHeaderOnlyLibrary
    SConsEnvironment.CreateTest = CreateTest
    #TODO: re-enable this
    #SConsEnvironment.CreateAutoToolsProject = CreateAutoToolsProject
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
            env.cprint('[warn] component tried to be re-added %s' % component.name, 'red')
    
    def get(self, name):
        if self.components.has_key(name):
            return self.components[name]
        else:
            return None
        
    def getComponentsNames(self):
        return self.components.keys()

componentGraph = ComponentDictionary()

class Component(object):
    def __init__(self, name, type, compDir, inc = [], deps = [], extInc = None):
        self.name = name
        self.type = type
        self.inc = []
        if inc:
            if isinstance(inc,list) or isinstance(inc,tuple):
                for i in inc:
                    self.inc.append( os.path.relpath(i.abspath, compDir.abspath) )
            else:
                self.inc.append( os.path.relpath(inc.abspath, compDir.abspath) )
        self.extInc = []
        if extInc:
            if isinstance(extInc,list) or isinstance(extInc,tuple):
                for i in extInc:
                    self.extInc.append( os.path.relpath(i.abspath, compDir.abspath) )
            else:
                self.extInc.append( os.path.relpath(extInc.abspath, compDir.abspath) )
        self.deps = deps
        # Directory where the component lives (the directory that contains the
        # SConscript)
        self.dir = compDir.abspath

    class Type:
        HEADER_ONLY = 0
        PROGRAM = 1
        UNITTEST = 2
        STATIC_LIBRARY = 3
        SHARED_LIBRARY = 4
        DOC = 5

    def GetDependenciesPaths(self, env):
        (incs, libs, libpaths, processedComponents) = self._getDependenciesPaths(env, [], 0)
        return (incs, libs, libpaths)
        
    def _getDependenciesPaths(self, env, processedComponents, depth):
        libpaths = []
        libs = []
        incs = []
        # First, add the stuff of this library so this goes first than the
        # dependencies
        if depth > 0 and (self.type in [Component.Type.DOC,
                                        Component.Type.PROGRAM,
                                        Component.Type.UNITTEST
                                        ]):
            env.cprint('[warn] %s depends on %s which is of type %s (this is not allowed)' 
                       % (processedComponents[len(processedComponents)-1],
                          self.name, 
                          self.type), 'yellow')
            return (incs, libs, libpaths, processedComponents) 
        if self.type in [Component.Type.STATIC_LIBRARY, 
                         Component.Type.SHARED_LIBRARY]:
            # We only link to this library if this is a component that another 
            # library depends on.
            if depth > 0:
                libs.append(self.name)
                libDir = os.path.join(env['BUILD_DIR'], self.name)
                libpaths.append(libDir)
        if self.type in [Component.Type.STATIC_LIBRARY, 
                         Component.Type.SHARED_LIBRARY,
                         Component.Type.HEADER_ONLY]:
            # We only include the external headers if this is a component
            # that another library depends on. If we are getting this library
            # every header should be in the inc section
            if depth > 0:
                for i in self.extInc:
                    hDir = os.path.join(env['INSTALL_HEADERS_DIR'], i)
                    incs.append(hDir)
            for i in self.inc:
                hDir = os.path.join(self.dir, i)
                incs.append(hDir)
        processedComponents.append(self.name)

        # Second step, get the paths from the dependencies. 
        # TODO: We need a way to check for circular dependencies
        for dep in self.deps:
            # Only process the dep if it was not already processed
            if not (dep in processedComponents):
                c = componentGraph.get(dep)
                if c is None:
                    env.cprint('[error] %s depends on %s which could not be found' % (self.name, dep), 'red')
                    continue
                (depIncs, depLibs, depLibPaths, depProcessedComp) = c._getDependenciesPaths(env,processedComponents,depth+1)
                libpaths.extend(depLibPaths)
                libs.extend(depLibs)
                incs.extend(depIncs)
        return (incs, libs, libpaths, processedComponents)

def CreateHeaderOnlyLibrary(env, name, ext_inc, deps):
    if isPreProcessing:
        componentGraph.add(env, Component(name,
                                          Component.Type.HEADER_ONLY,
                                          env.Dir('.'),
                                          [],
                                          deps,
                                          ext_inc
                                          ))
    else:
        hLib = RecursiveInstall(env, env.Dir('.'), ext_inc, name, headersFilter)
        env.Alias(name, hLib, 'Install ' + name + ' headers')
        env.Alias('all:install', hLib, "Install all targets")

def CreateProgram(env, name, inc, src, deps):
    if isPreProcessing:
        componentGraph.add(env, Component(name,
                                          Component.Type.PROGRAM,
                                          env.Dir('.'),
                                          inc,
                                          deps))
    else:
        (incpaths,libs,libpaths) = componentGraph.get(name).GetDependenciesPaths(env)
        prog = env.Program(name, src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)

        #allDeps = componentGraph.get(name).deps
        #for dep in allDeps:
        #    env.Depends(prog, env.HookedAlias(dep))

        env.Alias('all:build', prog, "Build all targets")
        
        iProg = env.Install(env['INSTALL_BIN_DIR'], prog)
        env.Alias(name, iProg, "Build and install " + name)
        env.Alias('all:install', iProg, "Install all targets")
    
def CreateTest(env, name, inc, src, deps):
    testName = name + ':test'
    if isPreProcessing:
        componentGraph.add(env, Component(testName,
                                          Component.Type.UNITTEST,
                                          env.Dir('.'),
                                          inc,
                                          deps))
    else:
        (incpaths,libs,libpaths) = componentGraph.get(testName).GetDependenciesPaths(env)
        tProg = env.Program(testName, src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        
        #allDeps = componentGraph.get(testName).deps
        #for dep in allDeps:
        #    env.Depends(tProg, env.HookedAlias(dep))
        
        env.Alias('all:build', tProg, "Build all targets")
        
        tTest = env.RunUnittest(testName + '.passed', tProg)
        env.Alias(testName, tTest, "Run test for " + name)
        env.Alias('all:test', tTest, "Run all tests")
    
def CreateStaticLibrary(env, name, inc, ext_inc, src, deps):
    if isPreProcessing:
        componentGraph.add(env, Component(name,
                                          Component.Type.STATIC_LIBRARY,
                                          env.Dir('.'),
                                          inc,
                                          deps,
                                          ext_inc))
    else:
        hLib = RecursiveInstall(env, env.Dir('.'), ext_inc, name, headersFilter)
        env.Alias('all:install', hLib, "Install all targets")
        
        (incpaths,libs,libpaths) = componentGraph.get(name).GetDependenciesPaths(env)
        
        #allDeps = componentGraph.get(name).deps
        #for dep in allDeps:
        #    env.Depends(hLib, env.HookedAlias(dep))
            
        sLib = env.Library(name, src, CPPPATH=incpaths)
        env.Alias(name, sLib, "Build " + name)
        env.Alias('all:build', sLib, "install all targets")
    
def CreateSharedLibrary(env, name, inc, ext_inc, src, deps):
    if isPreProcessing:
        componentGraph.add(env, Component(name,
                                          Component.Type.SHARED_LIBRARY,
                                          env.Dir('.'),
                                          inc,
                                          deps,
                                          ext_inc))
    else:
        hLib = RecursiveInstall(env, env.Dir('.'), ext_inc, name, headersFilter)
        env.Alias('all:install', hLib, "Install all targets")
        
        (incpaths,libs,libpaths) = componentGraph.get(name).GetDependenciesPaths(env)

        #allDeps = componentGraph.get(name).deps
        #for dep in allDeps:
        #    env.Depends(hLib, env.HookedAlias(dep))
            
        dLib = env.SharedLibrary(name, src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        iLib = env.Install(env['INSTALL_BIN_DIR'], dLib)
        env.Alias(name, iLib, "Build and install " + name)
        env.Alias('all:build', sLib, "install all targets")
    
#def CreateAutoToolsProject(env, name, libfile, configureFile, ext_inc):
#    if isPreProcessing:
#        componentGraph.add(env, Component(name))
    
def CreateDoc(env, name, doxyfile=None):
    docName = name + ':doc'
    if isPreProcessing:
        componentGraph.add(env, Component(docName,
                                          Component.Type.DOC,
                                          env.Dir('.')))
    else:
        if doxyfile == None:
            doxyfile = env.Glob('SConscript')
        targetDocDir = env.Dir(env['INSTALL_DOC_DIR']).Dir(name)
        doc = env.RunDoxygen(targetDocDir, doxyfile)
        env.Clean(doc, targetDocDir)
        env.Alias(docName, doc, 'Generate documentation for ' + name)
        
        allDeps = componentGraph.get(name).deps
        for dep in allDeps:
            env.Depends(doc, env.HookedAlias(dep))

def WalkDirsForSconscripts(env, topdir, ignore = []):
    global isPreProcessing
    global componentGraph
    global downloadDependencies
    
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
        for component in componentGraph.getComponentsNames():
            c = componentGraph.get(component)
            if c == None:
                # check if we know how to download this component
                env.CheckoutDependencyNow(component)
                downloadedDependencies = True
            else:
                for dep in c.deps:
                    cdep = componentGraph.get(dep)
                    if cdep == None:
                        env.CheckoutDependencyNow(dep)
                        downloadedDependencies = True
                        break
            # If a dependency was downloaded we need to re-parse all the
            # SConscripts to assurance not to try to download something that
            # is added by another component (i.e.: gtest_main is added by gmock)
            if downloadedDependencies:
                break
        if downloadedDependencies:
            # reset this to allow it to reparse those that were already added
            componentGraph = ComponentDictionary()

    # Step 2: real processing we have everything loaded in the dependency graph
    # now we process it
    isPreProcessing = False
    for root, dirnames, filenames in os.walk(topdir):
        if ignore.count(os.path.relpath(root, topdir)) == 0:
            for filename in fnmatch.filter(filenames, 'SConscript'):
                pathname = os.path.join(root, filename)
                env.SConscript(pathname, 
                               exports='env')

