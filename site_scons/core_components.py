# fudepan-build: The build system for FuDePAN projects
#
# Copyright (C) 2011-2012 Esteban Papp, Hugo Arregui, 2013 Gonzalo Bonigo, FuDePAN
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
        self.projDir = os.path.join(env['WS_DIR'], os.path.relpath(self.dir, env['BUILD_DIR']))

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
        return (libs, utils.removeDuplicates(libpaths))

    def _getLibs(self, processedComponents, depth):
        libpaths = []
        libs = []
        if self.shouldBeLinked and depth > 0:
            if not self.name in libs:
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
            for i in self.extInc:
                incs.append(os.path.join(self.env['WS_DIR'],
                                   os.path.relpath(i.abspath,self.env['BUILD_DIR'])))

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
    
    def _create_cccc_target(self, sources):
        # Create the 'target', it is the directory where the result will be put.
        target = self.env.Dir(self.env['INSTALL_METRICS_DIR']).Dir('cccc').Dir(self.name)
        # Set the name of the report file.
        outdir = target.abspath + os.sep
        self.env.Append(CCCC_OPTIONS='--html_outfile='+outdir+'MainHTMLReport')
        # Call RunCCCC().
        cccc = self.env.RunCCCC(target, sources)
        self.env.AlwaysBuild(cccc)
        # Create an alias to be show when run 'fbuild targets'.
        self.env.Alias(self.name+":cccc", cccc, 'Generate software metrics for %s' % self.name)
    
    def _create_cloc_target(self, sources):
        # Create the 'target', it is the directory where the result will be put.
        target = self.env.Dir(self.env['INSTALL_METRICS_DIR']).Dir('cloc').Dir(self.name)
        # Set the name of the report file.
        outdir = target.abspath
        if self.env['CLOC_OUTPUT_FORMAT'] == 'txt':
            self.env.Append(CLOC_OPTIONS = '--out=%s/CLOCMainTXTReport' % outdir)
        elif self.env['CLOC_OUTPUT_FORMAT'] == 'sql':
            self.env.Append(CLOC_OPTIONS = '--sql=%s/CLOCMainSQLReport' % outdir)
        elif self.env['CLOC_OUTPUT_FORMAT'] == 'xml':
            self.env.Append(CLOC_OPTIONS = '--xml --out=%s/CLOCMainXMLReport' % outdir)
        else:
            raise ValueError("Not valid value for CLOC_OUTPUT_FORMAT",self.env['CLOC_OUTPUT_FORMAT'])
        # Call RunCLOC().
        cloc = self.env.RunCLOC(target, sources)
        self.env.AlwaysBuild(cloc)
        # Create Componentan alias to be show when run 'fbuild targets'.
        self.env.Alias(self.name+":cloc", cloc, 'Generate software metrics for %s' % self.name)
    
    def _create_cppcheck_target(self, sources):
        # Create the 'target', it is the directory where the result will be put.
        target = self.env.Dir(self.env['INSTALL_METRICS_DIR']).Dir('cppcheck').Dir(self.name)
        # Call RunCppCheck().
        cppcheck = self.env.RunCppCheck(target, sources)
        self.env.AlwaysBuild(cppcheck)
        # Create an alias to be show when run 'fbuild targets'.
        self.env.Alias(self.name+":cppcheck", cppcheck, 'C/C++ code analyse for %s' % self.name)
    
    def _create_doc_target(self):
        targetDocDir = self.env.Dir(self.env['INSTALL_DOC_DIR']).Dir(self.name)
        doxyfile = self.env.File(self.env.Dir('#').abspath+'/conf/doxygenTemplate')
        doc = self.env.RunDoxygen(targetDocDir, doxyfile)
        self.env.Clean(doc, targetDocDir)
        self.env.Alias(self.name+':doc', doc, 'Generate documentation for ' + self.name)

    def Process(self, called_from_subclass=False):
        Component.Process(self)
        # Create target for generate the documentation.
        self._create_doc_target()
        # This condition is for the cases when the method is called from a subclass.
        if not called_from_subclass:
            # Create the list of the 'sources' files.
            sources = []
            for d in self.extInc:
                sources.extend(findFiles(self.env, d,['*.h']))
            self._create_cccc_target(sources)
            self._create_cloc_target(sources)
            self._create_cppcheck_target(sources)
        # We add astyle to all the components that can have a header (includes
        # the ones that have source)
        filters = []
        filters.extend(headersFilter)
        filters.extend(sourceFilters)
        sources = utils.files_flatten(self.env, self.projDir, filters)
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
        self.inc_paths = []
        if inc:
            if isinstance(inc, (list, tuple)):
                for i in inc:
                    self.inc_paths.append(i.abspath)
                    self.inc.append( os.path.relpath(i.abspath, compDir.abspath) )
            else:
                self.inc_paths.append(inc.abspath)
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
        # Create list sources and headers files
        self.src_files = []
        self.inc_files = self._get_include_files()
        for x in self.src:
            self.src_files.append(self.env.File(x))

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
                hDir = os.path.join(self.projDir, i)
                incs.append(hDir)
        return (incs, processedComponents)

    def getLibs(self):
        (libs, libpaths, processedComponents) = self._getLibs([], 0)
        return (libs, utils.removeDuplicates(libpaths))

    def _getLibs(self, processedComponents, depth):
        libpaths = []
        libs = []
        if self.shouldBeLinked and depth > 0:
            if not self.name in libs:
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
    
    def _get_include_files (self):
        include_files = []
        for i in self.inc:
            hDir = os.path.join(self.projDir, i)
            if hDir.endswith('/.'):
                hDir = hDir.replace('/.','/')
            for p in [hDir+x for x in headersFilter]:
                include_files.extend(self.env.Glob(p))
        return include_files

    def Process(self):
        HeaderOnlyComponent.Process(self,True)
        # Create the list of the 'sources' files.
        sources = self.src_files + self.inc_files
        self._create_cccc_target(sources)
        self._create_cloc_target(sources)
        self._create_cppcheck_target(sources)


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
        target = os.path.join(self.env['INSTALL_LIB_DIR'], self.name)
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

        # Should it be a call to ProgramComponent.Process() ??
        # Right now we do not need a call like that, because we don't want 
        # 'astyle', 'cccc', 'cloc' nether 'cppcheck' for test.
        # SourcedComponent.Process(self)

        incpaths = self.getIncludePaths()
        (libs,libpaths) = self.getLibs()
        target = os.path.join(self.dir, self.name)

        prog = self.env.Program(target, self.find_sources(), CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        self.env.Alias(self.name, prog, "Build and install " + self.name)
        self.env.Alias('all:build', prog, "Build all targets")

        target = os.path.join(self.dir, self.name + '.passed')
        tTest = self.env.RunUnittest(target, prog)

        # Adding valgrind for tests.
        if self.name.endswith(':test'):
            name = self.name.split(':')[0]
            vtname = '%s:valgrind' % name
        else:
            name = self.name
            vtname = '%s:valgrind' % name
        tvalg = os.path.join(self.env['INSTALL_LIB_DIR'], self.name)
        rvalg = self.env.RunValgrind(vtname, prog)
        self.env.Alias(vtname, [tTest,rvalg], 'Run valgrind for %s test' % name)

        if self.env.GetOption('gcoverage'):
            project = self.componentGraph.get(self.name.split(':')[0])
            self.env['PROJECT_DIR'] = project.dir
            initLcov = self.env.InitLcov(os.path.join(self.dir, 'coverage_data'), prog)
            self.env.Depends(tTest, initLcov)
            lcov = self.env.RunLcov(os.path.join(self.dir, 'lcov_output/index.html'), prog)
            self.env.Depends(lcov, tTest)
            self.env.AlwaysBuild(tTest)
            self.env.Alias(self.name, lcov)

        if self.env.GetOption('forcerun'):
            self.env.AlwaysBuild(tTest)

        self.env.Alias(self.name, tTest, "Run test for " + self.name)

        for refFile in findFiles(self.env, self.compDir.Dir('ref')):
            self.env.Depends(tTest, refFile)
        self.env.Alias('all:test', tTest, "Run all tests")

        for alias in self.aliasGroups:
            self.env.Alias(alias, tTest, "Build group " + alias)

    def getIncludePaths(self):
        includes = super(UnitTestComponent, self).getIncludePaths()
        project = self.componentGraph.get(self.name.split(':')[0])
        #adding current test dir
        filtered_includes = [self.dir, project.dir]
        #adding project in test include path (relative to build dir)
        for i in getattr(project, 'inc', []):
            filtered_includes.append(os.path.join(project.dir, i))
            filtered_includes.append(os.path.join(project.projDir, i))
        prjInstallPath = os.path.join(self.env['INSTALL_HEADERS_DIR'], project.name)
        for i in includes:
            path = os.path.realpath(i)
            in_build_dir = self.env['BUILD_DIR'] in path
            is_tested_project = project.dir in path or project.projDir in path or prjInstallPath in path
            if not in_build_dir and not is_tested_project:
                filtered_includes.append(path)
        return filtered_includes
