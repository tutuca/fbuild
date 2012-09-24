# fudepan-build: The build system for FuDePAN projects
#
# Copyright (C) 2011-2012 Esteban Papp, Hugo Arregui FuDePAN
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

import os
import utils
from utils import RecursiveInstall, findFiles

headersFilter = ['*.h','*.hpp']
sourceFilters = ['*.c','*.cpp','*.cc']

class Component(object):
    def __init__(self, componentGraph, env, name, compDir, deps, aliasGroups):
        self.name = name
        # Directory where the component lives (the directory that contains the
        # SConscript)
        self.compDir = compDir
        self.dir = compDir.abspath
        self.deps = deps
        self.env = env.Clone()
        self.aliasGroups = aliasGroups
        self.componentGraph = componentGraph

    def Process(self):
        return None

class ExternalLibraryComponent(Component):
    def __init__(self, componentGraph, env, name, compDir, deps, extInc, shouldBeLinked, aliasGroups):
        Component.__init__(self, componentGraph, env, name, compDir, deps, aliasGroups)
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
            if dep not in processedComponents:
                c = self.componentGraph.get(dep)
                if c is None:
                    self.env.cerror('[error] %s depends on %s which could not be found' % (self.name, dep))
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
            incs.extend([i.abspath for i in self.extInc])

        processedComponents.append(self.name)

        for dep in self.deps:
            # Only process the dep if it was not already processed
            if dep not in processedComponents:
                c = self.componentGraph.get(dep)
                if c is None:
                    self.env.cerror('[error] %s depends on %s which could not be found' % (self.name, dep))
                    continue
                (depIncs, depProcessedComp) = c._getIncludePaths(processedComponents,depth+1)
                incs.extend(depIncs)
        return (incs, processedComponents)

    def Process(self):
        return Component.Process(self)

class HeaderOnlyComponent(Component):
    def __init__(self, componentGraph, env, name, compDir, deps, extInc, aliasGroups):
        Component.__init__(self, componentGraph, env, name, compDir, deps, aliasGroups)
        self.extInc = []
        if extInc:
            if isinstance(extInc, (list, tuple)):
                self.extInc.extend(extInc)
            else:
                self.extInc.append(extInc)

    def getIncludePaths(self):
        (incs, processedComponents) = self._getIncludePaths([], 0)
        return incs

    def _getIncludePaths(self, processedComponents, depth):
        includeModulePath = os.path.join(self.env['INSTALL_HEADERS_DIR'], self.name)
        incs = []
        if depth > 0:
            for i in self.extInc:
                rel = os.path.relpath(i.abspath, self.compDir.abspath)
                hDir = os.path.join(includeModulePath, rel)
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
            if dep not in processedComponents:
                c = self.componentGraph.get(dep)
                if c is None:
                    self.env.cerror('[error] %s depends on %s which could not be found' % (self.name, dep))
                    continue
                if hasattr(c, '_getIncludePaths'):
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
            hLib = RecursiveInstall(self.env, self.compDir, self.extInc, self.name, headersFilter)
            self.env.Alias(self.name, hLib, 'Install ' + self.name + ' headers')
            self.env.Clean(self.name, hLib)
            self.env.Alias('all:install', hLib, "Install all targets")
            for alias in self.aliasGroups:
                self.env.Alias(alias, hLib, "Build group " + alias)
            return hLib
        else:
            return None

class SourcedComponent(HeaderOnlyComponent):
    def __init__(self, componentGraph, env, name, compDir, deps, inc, extInc, src, aliasGroups):
        HeaderOnlyComponent.__init__(self, componentGraph, env, name, compDir, deps, extInc, aliasGroups)
        self.inc = []
        if inc:
            if isinstance(inc, (list, tuple)):
                for i in inc:
                    self.inc.append( os.path.relpath(i.abspath, compDir.abspath) )
            else:
                self.inc.append( os.path.relpath(inc.abspath, compDir.abspath) )
        self.src = []
        if src:
            if isinstance(src, (list, tuple)):
                for s in src:
                    if isinstance(s, str):
                        self.src.append(os.path.abspath(s))
                    elif isinstance(s, (list, tuple)):
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
                projDir = os.path.join(self.env['WS_DIR'], os.path.relpath(self.dir,self.env['BUILD_DIR']))
                hDir = os.path.join(projDir, i)
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
            if dep not in processedComponents:
                c = self.componentGraph.get(dep)
                if c is None:
                    self.env.cerror('[error] %s depends on %s which could not be found' % (self.name, dep))
                    continue
                if hasattr(c, '_getLibs'):
                    (depLibs, depLibPaths, depProcessedComp) = c._getLibs(processedComponents,depth+1)
                    libpaths.extend(depLibPaths)
                    libs.extend(depLibs)
        return (libs, libpaths, processedComponents)

    def Process(self):
        HeaderOnlyComponent.Process(self)

class StaticLibraryComponent(SourcedComponent):
    def __init__(self, componentGraph, env, name, compDir, deps, inc, extInc, src, aliasGroups):
        SourcedComponent.__init__(self, componentGraph, env, name, compDir, deps, inc, extInc, src, aliasGroups)
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

class DynamicLibraryComponent(SourcedComponent):
    def __init__(self, componentGraph, env, name, compDir, deps, inc, extInc, src, aliasGroups):
        SourcedComponent.__init__(self, componentGraph, env, name, compDir, deps, inc, extInc, src, aliasGroups)
        self.shouldBeLinked = True

    def Process(self):
        SourcedComponent.Process(self)
        incpaths = self.getIncludePaths()
        (libs,libpaths) = self.getLibs()
        target = os.path.join(self.dir, self.name)
        dLib = self.env.SharedLibrary(target, self.src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        iLib = self.env.Install(self.env['INSTALL_LIB_DIR'], dLib)
        self.env.Alias(self.name, iLib, "Build and install " + self.name)
        self.env.Alias('all:build', dLib, "build all targets")
        self.env.Alias('all:install', iLib, "Install all targets")
        for alias in self.aliasGroups:
            self.env.Alias(alias, iLib, "Build group " + alias)
        return dLib

class ObjectComponent(SourcedComponent):
    def __init__(self, componentGraph, env, name, compDir, deps, inc, src, aliasGroups):
        SourcedComponent.__init__(self, componentGraph, env, name, compDir, deps, inc, [], src, aliasGroups)
        self.shouldBeLinked = False
        self.objs = []

    def Process(self):
        if not self.objs:
            SourcedComponent.Process(self)
            incpaths = self.getIncludePaths()

            (libs,libpaths) = self.getLibs()
            target = os.path.join(self.dir, self.name)
            for src in self.src:
                target = src.split('.')[0]
                obj = self.env.Object(target, src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
                self.objs.append(obj)
        return self.objs

class ProgramComponent(SourcedComponent):
    def __init__(self, componentGraph, env, name, compDir, deps, inc, src, aliasGroups):
        SourcedComponent.__init__(self, componentGraph, env, name, compDir, deps, inc, [], src, aliasGroups)
        self.shouldBeLinked = False

    def Process(self):
        SourcedComponent.Process(self)
        incpaths = self.getIncludePaths()

        (libs,libpaths) = self.getLibs()
        target = os.path.join(self.dir, self.name)
        prog = self.env.Program(target, self.find_sources(), CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        iProg = self.env.Install(self.env['INSTALL_BIN_DIR'], prog)
        self.env.Alias(self.name, iProg, "Build and install " + self.name)
        self.env.Alias('all:build', prog, "Build all targets")
        self.env.Alias('all:install', iProg, "Install all targets")
        for alias in self.aliasGroups:
            self.env.Alias(alias, iProg, "Build group " + alias)
        return prog

    def find_sources(self):
        src = self.src
        for dep in self.deps:
            c = self.componentGraph.get(dep)
            if isinstance(c, ObjectComponent):
                src.extend(c.Process())
        return src

class UnitTestComponent(ProgramComponent):
    def __init__(self, componentGraph, env, name, compDir, deps, inc, src, aliasGroups):
        ProgramComponent.__init__(self, componentGraph, env, name, compDir, deps, inc, src, aliasGroups)

    def Process(self):
        #gtest/gmock flags
        CXXFLAGS = [f for f in self.env['CXXFLAGS'] if f not in ['-ansi', '-pedantic']]
        CXXFLAGS.append('-Wno-sign-compare')
        self.env.Replace(CXXFLAGS=CXXFLAGS, CFLAGS=CXXFLAGS)

        SourcedComponent.Process(self)

        incpaths = self.getIncludePaths()
        (libs,libpaths) = self.getLibs()
        target = os.path.join(self.dir, self.name)

        prog = self.env.Program(target, self.find_sources(), CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        self.env.Alias(self.name, prog, "Build and install " + self.name)
        self.env.Alias('all:build', prog, "Build all targets")

        target = os.path.join(self.dir, self.name + '.passed')
        tTest = self.env.RunUnittest(target, prog)

        if self.env.GetOption('gcoverage'):
            projDir = os.path.join(self.env['WS_DIR'],
                                   os.path.relpath(self.dir,self.env['BUILD_DIR']))
            target = os.path.join(self.dir, 'lcov_output/index.html')
            lcov = self.env.RunLcov(target, prog)
            self.env.AlwaysBuild(lcov)
            self.env.Depends(lcov, tTest)
            self.env.Alias(self.name, lcov)
        
        if self.env.GetOption('forcerun'):
            self.env.AlwaysBuild(tTest)
        self.env.Alias(self.name, tTest, "Run test for " + self.name)

        for refFile in findFiles(self.env, self.compDir.Dir('ref')):
            self.env.Depends(tTest, refFile)
        self.env.Alias('all:test', tTest, "Run all tests")

        for alias in self.aliasGroups:
            self.env.Alias(alias, tTest, "Build group " + alias)
    
    #coverage is measured in build dir, so i put it first in the search path
    def getIncludePaths(self):
        includes = super(UnitTestComponent, self).getIncludePaths()
        original = self.componentGraph.get(self.name.split(':')[0])
        includes = [original.dir, self.dir] + [ i for i in includes if self.env['BUILD_DIR'] not in i]
        return includes
