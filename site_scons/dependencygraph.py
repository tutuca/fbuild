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
import utils
import SCons

downloadedDependencies = False

headersFilter = ['*.h','*.hpp']

def init(env):
    from SCons.Script.SConscript import SConsEnvironment
    SConsEnvironment.CreateProgram = CreateProgram
    SConsEnvironment.CreateLibraryComponent = CreateLibraryComponent
    SConsEnvironment.CreateStaticLibrary = CreateStaticLibrary
    SConsEnvironment.CreateSharedLibrary = CreateSharedLibrary
    SConsEnvironment.CreateHeaderOnlyLibrary = CreateHeaderOnlyLibrary
    SConsEnvironment.CreateTest = CreateTest
    #TODO: re-enable this
    #SConsEnvironment.CreateAutoToolsProject = CreateAutoToolsProject
    SConsEnvironment.CreateDoc = CreateDoc

class ComponentDictionary:
    components = {}
    
    def add(self, component):
        if not component.name.lower() == component.name:
            component.env.cprint('[warn] modules names should be lower case: ' + name, 'yellow')
        # Its possible that a component is tried to be added twice because a new
        # dependency was downloaded and 
        if not self.components.has_key(component.name):
            self.components[component.name] = component
        else:
            component.env.cprint('[warn] component tried to be re-added %s' % component.name, 'red')
    
    def get(self, name):
        if self.components.has_key(name):
            return self.components[name]
        else:
            return None
        
    def getComponentsNames(self):
        return self.components.keys()

componentGraph = ComponentDictionary()

class Component(object):
    def __init__(self, env, name, compDir, deps):
        self.name = name
        # Directory where the component lives (the directory that contains the
        # SConscript)
        self.dir = compDir.abspath
        self.deps = deps
        self.env = env

    def Process(self):
        for dep in self.deps:
            self.env.Depends(self.env.HookedAlias(self.name), self.env.HookedAlias(dep))

class HeaderOnlyComponent(Component):
    def __init__(self, env, name, compDir, deps, extInc):
        Component.__init__(self, env, name, compDir, deps)
        self.extInc = []
        if extInc:
            if isinstance(extInc,list) or isinstance(extInc,tuple):
                for i in extInc:
                    self.extInc.append( os.path.relpath(i.abspath, compDir.abspath) )
            else:
                self.extInc.append( os.path.relpath(extInc.abspath, compDir.abspath) )
    
    def getIncludePaths(self):
        (incs, processedComponents) = self._getIncludePaths([], 0)
        incs = utils.removeDuplicates(incs)
        return incs
    
    def _getIncludePaths(self, processedComponents, depth):
        includeModulePath = os.path.join(self.env['INSTALL_HEADERS_DIR'],self.name)
        incs = []
        if depth > 0:
            for i in self.extInc:
                hDir = os.path.join(includeModulePath, i)
                (hDirHead, hDirTail) = os.path.split(hDir)
                incs.append(hDirHead)
        # Because we are building from #, we include also compDir as an include
        # path so it finds local includes
        incs.append(self.dir)
        processedComponents.append(self.name)
        # Some modules export env.Dir('.') as a path, in those cases, we
        # need to include env['INSTALL_HEADERS_DIR'] as include path, this is
        # dangerous since it will be possible to refer to other modules
        incs.append(self.env['INSTALL_HEADERS_DIR'])
        
        # TODO: We need a way to check for circular dependencies
        for dep in self.deps:
            # Only process the dep if it was not already processed
            if not (dep in processedComponents):
                c = componentGraph.get(dep)
                if c is None:
                    dep.env.cprint('[error] %s depends on %s which could not be found' % (self.name, dep), 'red')
                    continue
                (depIncs, depProcessedComp) = c._getIncludePaths(processedComponents,depth+1)
                incs.extend(depIncs)
        return (incs, processedComponents)
    
    def Process(self):
        Component.Process(self)
        hLib = RecursiveInstall(self.env, self.dir, self.extInc, self.name, headersFilter)
        self.env.Alias(self.name, hLib, 'Install ' + self.name + ' headers')
        self.env.Alias('all:install', hLib, "Install all targets")
        return hLib

def CreateHeaderOnlyLibrary(env, name, ext_inc, deps):
    componentGraph.add(HeaderOnlyComponent(env,
                                           name,
                                           env.Dir('.'),
                                           deps,
                                           ext_inc))

class LibraryComponent(HeaderOnlyComponent):
    def __init__(self, env, name, compDir, deps, extInc, inc, src):
        HeaderOnlyComponent.__init__(self, env, name, compDir, deps, extInc)
        self.inc = []
        if inc:
            if isinstance(inc,list) or isinstance(inc,tuple):
                for i in inc:
                    self.inc.append( os.path.relpath(i.abspath, compDir.abspath) )
            else:
                self.inc.append( os.path.relpath(inc.abspath, compDir.abspath) )
        self.src = []
        if src:
            if isinstance(src, list):
                for s in src:
                    if isinstance(s, str):
                        self.src.append(os.path.abspath(s))
                    else:
                        self.src.append(os.path.abspath(compDir.rel_path(s)))
            else:
                if isinstance(src, str):
                    self.src.append(os.path.abspath(src))
                else:
                    self.src.append(os.path.abspath(compDir.rel_path(src)))
        
    def getIncludePaths(self):
        (incs, processedComponents) = self._getIncludePaths([], 0)
        return incs
    
    def _getIncludePaths(self, processedComponents, depth):
        incs = []
        (extIncs, processedComponents) = HeaderOnlyComponent._getIncludePaths(self, processedComponents, depth)
        incs.extend(extIncs)
        if depth == 0:
            # local headers can be referred explicitely (they are relative to the
            # current build directory) and are not from the install directory
            for i in self.inc:
                hDir = os.path.join(self.dir, i)
                incs.append(hDir)
        return (incs, processedComponents)
    
    def getLibs(self):
        (libs, libpaths, processedComponents) = self._getLibs([], 0)
        libs = utils.removeDuplicates(libs)
        libpaths = utils.removeDuplicates(libpaths)
        return (libs, libpaths)
        
    def _getLibs(self, processedComponents, depth):
        libpaths = []
        libs = []
        if depth > 0:
            libs.append(self.name)
            # For static libraries lookup:
            libpaths.append(self.env['INSTALL_LIB_DIR'])
            # For dynamic libraries lookup:
            libpaths.append(self.env['INSTALL_BIN_DIR'])
        processedComponents.append(self.name)

        # TODO: We need a way to check for circular dependencies
        for dep in self.deps:
            # Only process the dep if it was not already processed
            if not (dep in processedComponents):
                c = componentGraph.get(dep)
                if c is None:
                    self.env.cprint('[error] %s depends on %s which could not be found' % (self.name, dep), 'red')
                    continue
                if hasattr(c, '_getLibs'):
                    (depLibs, depLibPaths, depProcessedComp) = c._getLibs(processedComponents,depth+1)
                    libpaths.extend(depLibPaths)
                    libs.extend(depLibs)
        return (libs, libpaths, processedComponents)
    
    def Process(self):
        return HeaderOnlyComponent.Process(self)

def CreateLibraryComponent(env, name, ext_inc, deps):
    componentGraph.add(LibraryComponent(env,
                                        name,
                                        env.Dir('.'),
                                        deps,
                                        ext_inc,
                                        [],
                                        []))

class StaticLibraryComponent(LibraryComponent):
    def __init__(self, env, name, compDir, deps, extInc, inc, src):
        LibraryComponent.__init__(self, env, name, compDir, deps, extInc, inc, src)
    
    def Process(self):
        LibraryComponent.Process(self)
        incpaths = self.getIncludePaths()
        (libs,libpaths) = self.getLibs()
        sLib = self.env.StaticLibrary(self.name, self.src, CPPPATH=incpaths)
        iLib = self.env.Install(self.env['INSTALL_LIB_DIR'], sLib)
        self.env.Alias(self.name, sLib, "Build " + self.name)
        self.env.Alias('all:build', sLib, "build all targets")
        self.env.Alias('all:install', iLib, "Install all targets")
        return sLib

def CreateStaticLibrary(env, name, inc, ext_inc, src, deps):
    componentGraph.add(StaticLibraryComponent(env,
                                              name,
                                              env.Dir('.'),
                                              deps,
                                              ext_inc,
                                              inc,
                                              src))

class DynamicLibraryComponent(LibraryComponent):
    def __init__(self, env, name, compDir, deps, extInc, inc, src):
        LibraryComponent.__init__(self, env, name, compDir, deps, extInc, inc, src)
    
    def Process(self):
        LibraryComponent.Process(self)
        incpaths = self.getIncludePaths()
        (libs,libpaths) = self.getLibs()
        dLib = self.env.SharedLibrary(self.name, self.src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        iLib = self.env.Install(self.env['INSTALL_BIN_DIR'], dLib)
        self.env.Alias(self.name, iLib, "Build and install " + self.name)
        self.env.Alias('all:build', dLib, "build all targets")
        self.env.Alias('all:install', iLib, "Install all targets")
        return dLib

def CreateSharedLibrary(env, name, inc, ext_inc, src, deps):
    componentGraph.add(DynamicLibraryComponent(env,
                                               name,
                                               env.Dir('.'),
                                               deps,
                                               ext_inc,
                                               inc,
                                               src))

class ProgramComponent(LibraryComponent):
    def __init__(self, env, name, compDir, deps, inc, src):
        LibraryComponent.__init__(self, env, name, compDir, deps, [], inc, src)
    
    def Process(self):
        # TODO: add the header thing
        #LibraryComponent.Process(self)
        incpaths = self.getIncludePaths()
        (libs,libpaths) = self.getLibs()
        prog = self.env.Program(self.name, self.src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        iProg = self.env.Install(self.env['INSTALL_BIN_DIR'], prog)
        self.env.Alias(self.name, iProg, "Build and install " + self.name)
        self.env.Alias('all:build', prog, "Build all targets")
        self.env.Alias('all:install', iProg, "Install all targets")
        return prog

def CreateProgram(env, name, inc, src, deps):
    componentGraph.add(ProgramComponent(env,
                                        name,
                                        env.Dir('.'),
                                        deps,
                                        inc,
                                        src))

class UnitTestComponent(ProgramComponent):
    def __init__(self, env, name, compDir, deps, inc, src):
        ProgramComponent.__init__(self, env, name, compDir, deps, inc, src)

    def Process(self):
        prog = ProgramComponent.Process(self)
        tTest = self.env.RunUnittest(self.name + '.passed', prog)
        self.env.Alias(self.name, tTest, "Run test for " + self.name)
        self.env.Alias('all:test', tTest, "Run all tests")

def CreateTest(env, name, inc, src, deps):
    testName = name + ':test'
    # the test automatically depends on the thing that is testing
    deps.append(name)
    componentGraph.add(UnitTestComponent(env,
                                         testName,
                                         env.Dir('.'),
                                         deps,
                                         inc,
                                         src))

class DocComponent(Component):
    def __init__(self, env, name, compDir, doxyfile):
        Component.__init__(self, env, name, compDir, [])
        self.doxyfile = doxyfile
    
    def Process(self):
        Component.Process(self)
        targetDocDir = self.env.Dir(self.env['INSTALL_DOC_DIR']).Dir(self.name)
        doc = self.env.RunDoxygen(targetDocDir, self.doxyfile)
        self.env.Clean(doc, targetDocDir)
        self.env.Alias(self.name, doc, 'Generate documentation for ' + self.name)

def CreateDoc(env, name, doxyfile=None):
    docName = name + ':doc'
    if doxyfile == None:
        doxyfile = os.path.abspath(env['DEFAULT_DOXYFILE'])
    componentGraph.add(DocComponent(env,
                                    docName,
                                    env.Dir('.'),
                                    doxyfile))

#def CreateAutoToolsProject(env, name, libfile, configureFile, ext_inc):
#    if isPreProcessing:
#        componentGraph.add(env, Component(name))

def WalkDirsForSconscripts(env, topdir, ignore = []):
    global componentGraph
    
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
                        c.env.CheckoutDependencyNow(dep)
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
    for componentName in componentGraph.getComponentsNames():
        component = componentGraph.get(componentName)
        os.chdir(component.dir)
        component.Process()
