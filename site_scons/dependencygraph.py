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
sourceFilters = ['*.c','*.cpp','*.cc']

def init(env):
    from SCons.Script.SConscript import SConsEnvironment
    SConsEnvironment.CreateProgram = CreateProgram
    SConsEnvironment.CreateExternalLibraryComponent = CreateExternalLibraryComponent
    SConsEnvironment.CreateStaticLibrary = CreateStaticLibrary
    SConsEnvironment.CreateSharedLibrary = CreateSharedLibrary
    SConsEnvironment.CreateHeaderOnlyLibrary = CreateHeaderOnlyLibrary
    SConsEnvironment.CreateTest = CreateTest
    SConsEnvironment.CreateAutoToolsProject = CreateAutoToolsProject
    SConsEnvironment.CreateDoc = CreateDoc
    SConsEnvironment.CreatePdfLatex = CreatePdfLatex

class ComponentDictionary:
    components = {}

    def add(self, component, check = True):
        if check:
            if not component.name.lower() == component.name:
                component.env.cprint('[warn] modules names should be lower case: ' + component.name, 'yellow')
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
    def __init__(self, env, name, compDir, deps, aliasGroups):
        self.name = name
        # Directory where the component lives (the directory that contains the
        # SConscript)
        self.dir = compDir.abspath
        self.deps = deps
        self.env = env
        self.aliasGroups = aliasGroups

    def Process(self):
        return None

class ExternalLibraryComponent(Component):
    def __init__(self, env, name, compDir, deps, extInc, shouldBeLinked, aliasGroups):
        Component.__init__(self, env, name, compDir, deps, aliasGroups)
        self.extInc = []
        if extInc:
            if isinstance(extInc,list) or isinstance(extInc,tuple):
                for i in extInc:
                    self.extInc.append( i )
            else:
                self.extInc.append( extInc )
        self.shouldBeLinked = shouldBeLinked

    def getLibs(self):
        (libs, libpaths, processedComponents) = self._getLibs([], 0)
        return (utils.removeDuplicates(libs), utils.removeDuplicates(libpaths))

    def _getLibs(self, processedComponents, depth):
        libpaths = []
        libs = []
        if self.shouldBeLinked and depth > 0:
            libs.append(self.name)
            libpaths.append(self.dir)
        processedComponents.append(self.name)

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

    def getIncludePaths(self):
        (incs, processedComponents) = self._getIncludePaths([], 0)
        return utils.removeDuplicates(incs)

    def _getIncludePaths(self, processedComponents, depth):
        incs = []
        if depth > 0:
            incs.extend(self.extInc)

        processedComponents.append(self.name)

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
        return Component.Process(self)

def CreateExternalLibraryComponent(env, name, ext_inc, libPath, deps, shouldBeLinked, aliasGroups = []):
    componentGraph.add(ExternalLibraryComponent(env,
                                                name,
                                                libPath,
                                                deps,
                                                ext_inc,
                                                shouldBeLinked,
                                                aliasGroups),
                       False)

class HeaderOnlyComponent(Component):
    def __init__(self, env, name, compDir, deps, extInc, aliasGroups):
        Component.__init__(self, env, name, compDir, deps, aliasGroups)
        self.extInc = []
        if extInc:
            if isinstance(extInc,list) or isinstance(extInc,tuple):
                for i in extInc:
                    self.extInc.append( os.path.relpath(i.abspath, compDir.abspath) )
            else:
                self.extInc.append( os.path.relpath(extInc.abspath, compDir.abspath) )

    def getIncludePaths(self):
        (incs, processedComponents) = self._getIncludePaths([], 0)
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
        #incs.append(self.env['INSTALL_HEADERS_DIR'])

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

        # we add astyle to all the components that can have a header (includes
        # the ones that have source)
        filters = []
        filters.extend(headersFilter)
        filters.extend(sourceFilters)
        projDir = os.path.join(self.env['WS_DIR'],
                               os.path.relpath(self.dir,self.env['BUILD_DIR']))
        sources = utils.files_flatten(self.env, projDir, filters)
        target = self.env.Dir(self.env['BUILD_DIR']).Dir('astyle').Dir(self.name)
        astyleOut = self.env.RunAStyle(target, sources)
        self.env.Alias(self.name + ':astyle', astyleOut, "Runs astyle on " + self.name)

        # If the component doesnt have external headers, we dont process it since
        # there is nothing to install
        if len(self.extInc) > 0:
            hLib = RecursiveInstall(self.env, self.dir, self.extInc, self.name, headersFilter)
            self.env.Alias(self.name, hLib, 'Install ' + self.name + ' headers')
            self.env.Clean(self.name, hLib)
            self.env.Alias('all:install', hLib, "Install all targets")
            for alias in self.aliasGroups:
                self.env.Alias(alias, hLib, "Build group " + alias)
            return hLib
        else:
            return None

def CreateHeaderOnlyLibrary(env, name, ext_inc, deps, aliasGroups = []):
    componentGraph.add(HeaderOnlyComponent(env,
                                           name,
                                           env.Dir('.'),
                                           deps,
                                           ext_inc,
                                           aliasGroups))

class SourcedComponent(HeaderOnlyComponent):
    def __init__(self, env, name, compDir, deps, inc, extInc, src, aliasGroups):
        HeaderOnlyComponent.__init__(self, env, name, compDir, deps, extInc, aliasGroups)
        self.inc = []
        if inc:
            if isinstance(inc,list) or isinstance(inc,tuple):
                for i in inc:
                    self.inc.append( os.path.relpath(i.abspath, compDir.abspath) )
            else:
                self.inc.append( os.path.relpath(inc.abspath, compDir.abspath) )
        self.src = []
        if src:
            if isinstance(src, list) or isinstance(src,tuple):
                for s in src:
                    if isinstance(s, str):
                        self.src.append(os.path.abspath(s))
                    elif isinstance(s, list) or isinstance(s,tuple):
                        for subS in s:
                            self.src.append(os.path.abspath(compDir.rel_path(subS)))
                    else:
                        self.src.append(os.path.abspath(compDir.rel_path(s)))
            else:
                if isinstance(src, str):
                    self.src.append(os.path.abspath(src))
                else:
                    self.src.append(os.path.abspath(compDir.rel_path(src)))
        self.shouldBeLinked = False

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
        return (utils.removeDuplicates(libs), utils.removeDuplicates(libpaths))

    def _getLibs(self, processedComponents, depth):
        libpaths = []
        libs = []
        if self.shouldBeLinked and depth > 0:
            libs.append(self.name)
            # TODO: just add the one that matters here
            # For static libraries lookup:
            libpaths.append(self.env['INSTALL_LIB_DIR'])
            # For dynamic libraries lookup:
            libpaths.append(self.env['INSTALL_BIN_DIR'])
        processedComponents.append(self.name)

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
        HeaderOnlyComponent.Process(self)

class StaticLibraryComponent(SourcedComponent):
    def __init__(self, env, name, compDir, deps, inc, extInc, src, aliasGroups):
        SourcedComponent.__init__(self, env, name, compDir, deps, inc, extInc, src, aliasGroups)
        self.shouldBeLinked = True

    def Process(self):
        SourcedComponent.Process(self)
        incpaths = self.getIncludePaths()
        (libs,libpaths) = self.getLibs()
        target = os.path.join(self.dir, self.name)
        sLib = self.env.StaticLibrary(target, self.src, CPPPATH=incpaths)
        iLib = self.env.Install(self.env['INSTALL_LIB_DIR'], sLib)
        self.env.Alias(self.name, sLib, "Build " + self.name)
        self.env.Alias('all:build', sLib, "build all targets")
        self.env.Alias('all:install', iLib, "Install all targets")
        for alias in self.aliasGroups:
            self.env.Alias(alias, iLib, "Build group " + alias)
        return sLib

def CreateStaticLibrary(env, name, inc, ext_inc, src, deps, aliasGroups = []):
    componentGraph.add(StaticLibraryComponent(env,
                                              name,
                                              env.Dir('.'),
                                              deps,
                                              inc,
                                              ext_inc,
                                              src,
                                              aliasGroups))

class DynamicLibraryComponent(SourcedComponent):
    def __init__(self, env, name, compDir, deps, inc, extInc, src, aliasGroups):
        SourcedComponent.__init__(self, env, name, compDir, deps, inc, extInc, src, aliasGroups)
        self.shouldBeLinked = True

    def Process(self):
        SourcedComponent.Process(self)
        incpaths = self.getIncludePaths()
        (libs,libpaths) = self.getLibs()
        target = os.path.join(self.dir, self.name)
        dLib = self.env.SharedLibrary(target, self.src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        iLib = self.env.Install(self.env['INSTALL_BIN_DIR'], dLib)
        self.env.Alias(self.name, iLib, "Build and install " + self.name)
        self.env.Alias('all:build', dLib, "build all targets")
        self.env.Alias('all:install', iLib, "Install all targets")
        for alias in self.aliasGroups:
            self.env.Alias(alias, iLib, "Build group " + alias)
        return dLib

def CreateSharedLibrary(env, name, inc, ext_inc, src, deps, aliasGroups = []):
    componentGraph.add(DynamicLibraryComponent(env,
                                               name,
                                               env.Dir('.'),
                                               deps,
                                               inc,
                                               ext_inc,
                                               src,
                                               aliasGroups))

class ProgramComponent(SourcedComponent):
    def __init__(self, env, name, compDir, deps, inc, src, aliasGroups):
        SourcedComponent.__init__(self, env, name, compDir, deps, [], inc, src, aliasGroups)
        self.shouldBeLinked = False

    def Process(self):
        SourcedComponent.Process(self)
        incpaths = self.getIncludePaths()

        (libs,libpaths) = self.getLibs()
        target = os.path.join(self.dir, self.name)
        prog = self.env.Program(target, self.src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        iProg = self.env.Install(self.env['INSTALL_BIN_DIR'], prog)
        self.env.Alias(self.name, iProg, "Build and install " + self.name)
        self.env.Alias('all:build', prog, "Build all targets")
        self.env.Alias('all:install', iProg, "Install all targets")
        for alias in self.aliasGroups:
            self.env.Alias(alias, iProg, "Build group " + alias)
        return prog

def CreateProgram(env, name, inc, src, deps, aliasGroups = []):
    componentGraph.add(ProgramComponent(env,
                                        name,
                                        env.Dir('.'),
                                        deps,
                                        inc,
                                        src,
                                        aliasGroups))

class UnitTestComponent(ProgramComponent):
    def __init__(self, env, name, compDir, deps, inc, src, aliasGroups):
        ProgramComponent.__init__(self, env, name, compDir, deps, inc, src, aliasGroups)

    def Process(self):
        SourcedComponent.Process(self)

        incpaths = self.getIncludePaths()
        (libs,libpaths) = self.getLibs()
        target = os.path.join(self.dir, self.name)
        prog = self.env.Program(target, self.src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        self.env.Alias(self.name, prog, "Build and install " + self.name)
        self.env.Alias('all:build', prog, "Build all targets")

        target = os.path.join(self.dir, self.name + '.passed')
        tTest = self.env.RunUnittest(target, prog)
        if self.env.GetOption('forcerun'):
            self.env.AlwaysBuild(tTest)
        self.env.Alias(self.name, tTest, "Run test for " + self.name)
        self.env.Alias('all:test', tTest, "Run all tests")

        for alias in self.aliasGroups:
            self.env.Alias(alias, tTest, "Build group " + alias)

def CreateTest(env, name, inc, src, deps, aliasGroups = []):
    testName = name + ':test'
    # the test automatically depends on the thing that is testing
    if deps.count(name) == 0:
        deps.append(name)
    componentGraph.add(UnitTestComponent(env,
                                         testName,
                                         env.Dir('.'),
                                         deps,
                                         inc,
                                         src,
                                         aliasGroups))

class PdfLatexComponent(Component):
    def __init__(self, env, name, compDir, latexfile, aliasGroups):
        Component.__init__(self, env, name, compDir, [], aliasGroups)
        self.latexfile = latexfile

    def Process(self):
        Component.Process(self)
        targetDocDir = self.env.Dir(self.env['INSTALL_DOC_DIR']).Dir(self.name)
        pdf = self.env.RunPdfLatex(targetDocDir, self.latexfile)
        self.env.Clean(pdf, targetDocDir)
        self.env.Alias(self.name, pdf, 'Generate pdf from ' + self.latexfile
            + 'for ' + self.name)

        for alias in self.aliasGroups:
            self.env.Alias(alias, pdf, "Build group " + alias)

def CreatePdfLatex(env, name, latexfile = '', options='', aliasGroups = []):
    docName = name + ':pdf'
    env['PDFLATEX_OPTIONS'] = options
    componentGraph.add(PdfLatexComponent(env,
                                    docName,
                                    env.Dir('.'),
                                    latexfile,
                                    aliasGroups))

class DocComponent(Component):
    def __init__(self, env, name, compDir, doxyfile, aliasGroups):
        Component.__init__(self, env, name, compDir, [], aliasGroups)
        self.doxyfile = doxyfile

    def Process(self):
        Component.Process(self)
        targetDocDir = self.env.Dir(self.env['INSTALL_DOC_DIR']).Dir(self.name)
        doc = self.env.RunDoxygen(targetDocDir, self.doxyfile)
        self.env.Clean(doc, targetDocDir)
        self.env.Alias(self.name, doc, 'Generate documentation for ' + self.name)

        for alias in self.aliasGroups:
            self.env.Alias(alias, doc, "Build group " + alias)

def CreateDoc(env, name, doxyfile=None, aliasGroups = []):
    docName = name + ':doc'
    if doxyfile == None:
        doxyfile = os.path.abspath(env['DEFAULT_DOXYFILE'])
    componentGraph.add(DocComponent(env,
                                    docName,
                                    env.Dir('.'),
                                    doxyfile,
                                    aliasGroups))

class AutoToolsProject(Component):
    def __init__(self, env, name, compDir, configurationFile, aliasGroups):
        Component.__init__(self, env, name, compDir, [], aliasGroups)
        self.configurationFile = configurationFile

    def Process(self):
        Component.Process(self)
        targetMake = self.env.Dir(self.env['INSTALL_LIB_DIR']).Dir(self.name)
        make = self.env.RunMakeTool(targetMake, self.configurationFile)
        self.env.Clean(make, targetMake)
        self.env.Alias(self.name, make, 'Make ' + self.name)

        for alias in self.aliasGroups:
            self.env.Alias(alias, make, "Build group " + alias)

def CreateAutoToolsProject(env, name, libfile, configurationFile, aliasGroups = []):
    componentGraph.add(AutoToolsProject(env,
                                        name,
                                        env.Dir('.'),
                                        configurationFile,
                                        aliasGroups))

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
                    vdir = os.path.join(env['BUILD_DIR'],
                                        os.path.relpath(root,env['WS_DIR']))
                    env.SConscript(pathname,
                                   exports='env',
                                   variant_dir=vdir,
                                   duplicate=1)
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
        component.Process()
