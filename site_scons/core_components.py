# fudepan-build: The build system for FuDePAN projects
#
# Copyright (C) 2011-2012 Esteban Papp, Hugo Arregui, 
#               2013 Gonzalo Bonigo, Gustavo Ojeda FuDePAN
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
    Add a description here!
"""


import os
import sys
import utils


headersFilter = ['*.h','*.hpp']
sourceFilters = ['*.c','*.cpp','*.cc']


class CyclicDependencieError(Exception):
    """
        An exception that represents a cycle in the dependence graph.
    """
    pass


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
        self.shouldBeLinked = False

    def Process(self):
        return None
    
    def GetLibs(self):
        """
            Description:
                This method returns the libraries (and its paths) that should be 
                linked when the component have to be build.
            Arguments:
                None.
            Exceptions:
                None.
            Return:
                A tuple instance of the form (libs,libpaths) where 'libs' is the 
                list of the libraries and 'libpaths' the list of its paths.
        """
        # List of libraries.
        libs = []
        # List of libraries paths.
        libpaths = []
        # Append some strandars paths to this variable.
        libpaths.append(self.env['INSTALL_LIB_DIR'])
        libpaths.append(self.env['INSTALL_BIN_DIR'])
        # Look for the libs and its paths.
        try:
            self._GetLibs(libs, libpaths, [], 0)
        except CyclicDependencieError, error:
            msg = (' -> ').join(error[0])
            self.env.cerror('[error] A dependency cycle was found:\n  %s' % msg)
        # Remember:
        #   t[0]  ->  depth.
        #   t[1]  ->  name.
        # This function tells if the tuple depth (t[0]) is the maximum in libs.
        is_max = lambda t : len([x for x in libs if x[1]==t[1] and x[0]>t[0]]) == 0
        # This function tells if the tuple name (t[1]) is unique in libs.
        unique = lambda t : len([x for x in libs if x[1]==t[1]]) == 1
        # Remove from the list the duplicated names.
        aux = [t for t in libs if unique(t) or is_max(t)]; aux.sort()
        # Create the libs list.
        libs = [t[1] for t in aux]
        return (libs, libpaths)

    def _GetLibs(self, libs, libpaths, stack, depth):
        """
            This is a recursive internal method used by the self.getLibs() method.
        """
        if self.name in stack:
            # If the component name is within the stack then there is a cycle.
            stack.append(self.name)
            raise CyclicDependencieError(stack)
        else:
            # We add the component name to the stack.
            stack.append(self.name)
        if self.shouldBeLinked and depth > 0:
            libs.append((depth,self.name))
            # We add the directory where the library lives.
            if not self.dir in libpaths:
                libpaths.append(self.dir)
        # Check its dependencies.
        for dep in self.deps:
            c = self.componentGraph.get(dep)
            if c is None:
                self.env.cerror(
                    '[error] %s depends on %s which could not be found' % 
                    (self.name, dep)
                )
            else: #if not isinstance(c, HeaderOnlyComponent):
                c._GetLibs(libs, libpaths, stack, depth+1)
        # We remove the component name from the stack.
        if self.name in stack:
            stack.pop()


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

    def Process(self):
        return Component.Process(self)

    def GetIncludePaths(self):
        (incs, processedComponents) = self._GetIncludePaths([], 0)
        return utils.removeDuplicates(incs)

    def _GetIncludePaths(self, processedComponents, depth):
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
                (depIncs, depProcessedComp) = c._GetIncludePaths(processedComponents,depth+1)
                incs.extend(depIncs)
        return (incs, processedComponents)


class HeaderOnlyComponent(Component):
    
    def __init__(self, componentGraph, env, name, compDir, deps, extInc, aliasGroups):
        Component.__init__(self, componentGraph, env, name, compDir, deps, aliasGroups)
        self.extInc = []
        if extInc:
            if isinstance(extInc, (list, tuple)):
                self.extInc.extend(extInc)
            else:
                self.extInc.append(extInc)

    def Process(self, called_from_subclass=False):
        Component.Process(self)
        # Look for the sources of this component.
        filters = []
        filters.extend(headersFilter)
        filters.extend(sourceFilters)
        sources = utils.files_flatten(self.env, self.projDir, filters)
        # Create target for jenkins.
        self._create_jenkins_target()
        if not self.name.endswith(':test'):
            # Create target for generate the documentation.
            self._create_doc_target()
            # We add astyle target to all the components that can have a header.
            self._create_astyle_target(sources)
            # We add a traget for check if the component is astyled.
            self._create_astyle_check_target(sources)
            # This condition is for the cases when the method is called from a subclass.
            if not called_from_subclass:
                # Create the list of the 'sources' files.
                sources = []
                for d in self.extInc:
                    sources.extend(utils.FindFiles(self.env, d,['*.h']))
                self._create_cccc_target(sources)
                self._create_cloc_target(sources)
                self._create_cppcheck_target(sources)
            # If the component doesnt have external headers, we dont process it since
            # there is nothing to install
            if len(self.extInc) > 0:
                hLib = utils.RecursiveInstall(self.env, self.compDir, self.extInc, self.name, headersFilter)
                self.env.Alias(self.name, hLib, 'Install ' + self.name + ' headers')
                self.env.Clean(self.name, hLib)
                self.env.Alias('all:install', hLib, "Install all targets")
                for alias in self.aliasGroups:
                    self.env.Alias(alias, hLib, "Build group " + alias)
                return hLib
            else:
                return None

    def GetIncludePaths(self):
        (incs, processedComponents) = self._GetIncludePaths([], 0)
        return incs

    def _GetIncludePaths(self, processedComponents, depth):
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
                if hasattr(c, '_GetIncludePaths'):
                    (depIncs, depProcessedComp) = c._GetIncludePaths(processedComponents,depth+1)
                    incs.extend(depIncs)
        return (incs, processedComponents)
    
    def _create_cccc_target(self, sources):
        # Create the 'target', it is the directory where the result will be put.
        target = self.env.Dir(self.env['INSTALL_METRICS_DIR']).Dir('cccc').Dir(self.name)
        # Set the name of the report file.
        outdir = target.abspath + os.sep
        self.env.Append(CCCC_OPTIONS='--html_outfile='+outdir+'CCCCMainHTMLReport.html')
        # Call RunCCCC().
        cccc = self.env.RunCCCC(target, sources)
        self.env.AlwaysBuild(cccc)
        # Create an alias to be show when run 'fbuild targets'.
        self.env.Alias(self.name+":cccc", cccc, 'Generate software metrics for %s' % self.name)
        # Add dependence for jenkins.
        self.env.Depends(self.jenkins_target,cccc)
    
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
        # Add dependence for jenkins.
        self.env.Depends(self.jenkins_target,cloc)
    
    def _create_jenkins_target(self):
        # Create the target for jenkins.
        if self.name.endswith(':test'):
            name = self.name.split(':')[0]
        else:
            name = self.name
        self.jenkins_target = self.env.Alias('%s:jenkins' % name, None, '')
        self.env.AlwaysBuild(self.jenkins_target)
    
    def _create_cppcheck_target(self, sources):
        # Create the 'target', it is the directory where the result will be put.
        target = self.env.Dir(self.env['INSTALL_METRICS_DIR']).Dir('cppcheck').Dir(self.name)
        # Call RunCppCheck().
        cppcheck = self.env.RunCppCheck(target, sources)
        self.env.AlwaysBuild(cppcheck)
        # Create an alias to be show when run 'fbuild targets'.
        self.env.Alias(self.name+":cppcheck", cppcheck, 'C/C++ code analyse for %s' % self.name)
        # Add dependence for jenkins.
        self.env.Depends(self.jenkins_target,cppcheck)
    
    def _create_doc_target(self):
        targetDocDir = self.env.Dir(self.env['INSTALL_DOC_DIR']).Dir(self.name)
        doxyfile = self.env.File(self.env.Dir('#').abspath+'/conf/doxygenTemplate')
        sconscript = ('%s/SConscript' % self.dir).replace('/build/','/projects/')
        # We pass it the path to the SConscript file because we need the path to 
        # the project directory but we only can put 'env.File' objects as sources.
        doc = self.env.RunDoxygen(targetDocDir, [doxyfile,sconscript])
        self.env.Clean(doc, targetDocDir)
        self.env.Alias(self.name+':doc', doc, 'Generate documentation for ' + self.name)
        # Add dependence for jenkins.
        self.env.Depends(self.jenkins_target,doc)
    
    def _create_astyle_check_target(self, sources):
        # Create the target.
        target = self.env.Dir(self.env['BUILD_DIR']).Dir('astyle-check').Dir(self.name)
        # Call RunAStyleCheck().
        astyle_check = self.env.RunAStyleCheck(target, sources)
        self.env.AlwaysBuild(astyle_check)
        # Create info message.
        msg = "Checks if the project %s has been astyled." % self.name
        # Create an alias for the astyle checker.
        self.env.Alias('%s:astyle-check' % self.name, astyle_check, msg)
        # Add dependence for jenkins.
        self.env.Depends(self.jenkins_target,astyle_check)
    
    def _create_astyle_target(self, sources):
        # Create the target.
        target = self.env.Dir(self.env['BUILD_DIR']).Dir('astyle').Dir(self.name)
        # Call RunAStyle().
        astyleOut = self.env.RunAStyle(target, sources)
        # Create an alias for astyle.
        self.env.Alias('%s:astyle' % self.name, astyleOut, "Runs astyle on " + self.name)


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
        # Create list sources and headers files
        self.src_files = []
        self.inc_files = self._get_include_files()
        for x in self.src:
            self.src_files.append(self.env.File(x))

    def Process(self):
        HeaderOnlyComponent.Process(self,True)
        if not self.name.endswith(':test'):
            # Create the list of the 'sources' files.
            sources = self.src_files + self.inc_files
            self._create_cccc_target(sources)
            self._create_cloc_target(sources)
            self._create_cppcheck_target(sources)

    def GetIncludePaths(self):
        (incs, processedComponents) = self._GetIncludePaths([], 0)
        return incs

    def _GetIncludePaths(self, processedComponents, depth):
        incs = []
        (extIncs, processedComponents) = HeaderOnlyComponent._GetIncludePaths(self, processedComponents, depth)
        incs.extend(extIncs)
        if depth == 0:
            # local headers can be referred explicitely (they are relative to the
            # current build directory) and are not from the install directory
            for i in self.inc:
                hDir = os.path.join(self.projDir, i)
                incs.append(hDir)
        return (incs, processedComponents)

    def _get_include_files (self):
        include_files = []
        for i in self.inc:
            hDir = os.path.join(self.projDir, i)
            if hDir.endswith('/.'):
                hDir = hDir.replace('/.','/')
            for p in [hDir+x for x in headersFilter]:
                include_files.extend(self.env.Glob(p))
        return include_files


class StaticLibraryComponent(SourcedComponent):
    
    def __init__(self, componentGraph, env, name, compDir, deps, inc, extInc, src, aliasGroups):
        SourcedComponent.__init__(self, componentGraph, env, name, compDir, deps, inc, extInc, src, aliasGroups)
        self.shouldBeLinked = True

    def Process(self):
        SourcedComponent.Process(self)
        incpaths = self.GetIncludePaths()
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
        incpaths = self.GetIncludePaths()
        (libs,libpaths) = self.GetLibs()
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
        self.objs = []

    def Process(self):
        if not self.objs:
            SourcedComponent.Process(self)
            incpaths = self.GetIncludePaths()
            (libs,libpaths) = self.GetLibs()
            target = os.path.join(self.dir, self.name)
            for src in self.src:
                target = src.split('.')[0]
                obj = self.env.Object(target, src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
                self.objs.append(obj)
        return self.objs


class ProgramComponent(SourcedComponent):
    
    def __init__(self, componentGraph, env, name, compDir, deps, inc, src, aliasGroups):
        SourcedComponent.__init__(self, componentGraph, env, name, compDir, deps, inc, [], src, aliasGroups)

    def Process(self):
        SourcedComponent.Process(self)
        incpaths = self.GetIncludePaths()
        (libs,libpaths) = self.GetLibs()
        target = os.path.join(self.env['INSTALL_LIB_DIR'], self.name)
        self.prog = self.env.Program(target, self.findSources(), CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        iProg = self.env.Install(self.env['INSTALL_BIN_DIR'], self.prog)
        self.env.Alias(self.name, iProg, "Build and install " + self.name)
        self.env.Alias('all:build', self.prog, "Build all targets")
        self.env.Alias('all:install', iProg, "Install all targets")
        for alias in self.aliasGroups:
            self.env.Alias(alias, iProg, "Build group " + alias)
        return self.prog

    def findSources(self):
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
        # Call to super-super-class SourcedComponent().
        # We not call directly to the supper class ProgramComponent.Process() 
        # since it generates a problem when running the test executable.
        SourcedComponent.Process(self)
        # So, we have to call the Program() builder.
        incpaths = self.GetIncludePaths()
        (libs,libpaths) = self.GetLibs()
        target = os.path.join(self.dir, self.name)
        self.prog = self.env.Program(target, self.findSources(), CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        self.env.Alias(self.name, self.prog, "Build and install " + self.name)
        self.env.Alias('all:build', self.prog, "Build all targets")
        # Flags for gtest and gmock.
        CXXFLAGS = [f for f in self.env['CXXFLAGS'] if f not in ['-ansi', '-pedantic']]
        CXXFLAGS.append('-Wno-sign-compare')
        if not '-ggdb3' in CXXFLAGS:
            CXXFLAGS.append('-ggdb3')
        self.env.Replace(CXXFLAGS=CXXFLAGS, CFLAGS=CXXFLAGS)
        # Check if it needed to generate a test report.
        if utils.wasTargetInvoked('%s:jenkins' % self.name.split(':')[0]):
            gtest_report = self.env.Dir(self.env['INSTALL_METRICS_DIR']).Dir('test').Dir(self.name[:-5])
            self.env.gtest_report = 'xml:%s/test-report.xml' % gtest_report.abspath
        # File to store the test results.
        target = os.path.join(self.dir, self.name + '.passed')
        tTest = self.env.RunUnittest(target, self.prog)
        # Check if the user want to run the tests anyway.
        if self.env.GetOption('forcerun'):
            self.env.AlwaysBuild(tTest)
        # Create the target for the test.
        self.env.Alias(self.name, tTest, "Run test for " + self.name)
        # Make the test depends from coverage generated files.
        for refFile in utils.FindFiles(self.env, self.compDir.Dir('ref')):
            self.env.Depends(tTest, refFile)
        # Alias target for 'all'.
        self.env.Alias('all:test', tTest, "Run all tests")
        # Adding a valgrind target for tests.
        tvalg = self._CreateValgrindTarget(tTest)
        # Adding a coverage target for tests.
        tcov = self._CreateCoverageTarget(target)
        # Add dependence for jenkins.
        self.env.Depends(self.jenkins_target,[tvalg, tcov])
        # Create alias for aliasGroups.
        for alias in self.aliasGroups:
            self.env.Alias(alias, tTest, "Build group " + alias)

    def GetIncludePaths(self):
        includes = super(UnitTestComponent, self).GetIncludePaths()
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

    def _CreateValgrindTarget(self, tTest): 
        # Remove the ':test' from the name of the project.
        name = self.name.split(':')[0]
        vtname = '%s:valgrind' % name
        # Check if we need to create an xml report.
        if utils.wasTargetInvoked('%s:jenkins' % self.name.split(':')[0]):
            metrics_dir = self.env['INSTALL_METRICS_DIR']
            vdir = self.env.Dir(metrics_dir).Dir('valgrind').Dir(self.name)
            if not os.path.exists(vdir.abspath):
                os.makedirs(vdir.abspath)
            vreport = '%s/valgrind-report.xml' % vdir.abspath
            self.env.Append(VALGRIND_OPTIONS = ' --xml=yes --xml-file=%s ' % vreport)
        # Target for the RunValgrind() builder.
        tvalg = os.path.join(self.env['INSTALL_LIB_DIR'], self.name)
        # Call builder RunValgrind().
        rvalg = self.env.RunValgrind(vtname, self.prog)
        # Create an alias for valgrind.
        avalg = self.env.Alias(vtname, [tTest,rvalg], 'Run valgrind for %s test' % name)
        return avalg
        
    def _CreateCoverageTarget(self, target):
        # Get the path directory to the project.
        project = self.componentGraph.get(self.name.split(':')[0])
        self.env['PROJECT_DIR'] = project.dir
        # Check if the coverage is needed.
        if (utils.wasTargetInvoked('%s:jenkins' % self.name.split(':')[0]) or 
           utils.wasTargetInvoked('%s:coverage' % self.name.split(':')[0])) :
            gprofFlags = ['--coverage']
            self.env.Append(CXXFLAGS=gprofFlags, CFLAGS=gprofFlags, LINKFLAGS=gprofFlags)
        # Targets and sources for builder InitLcov.
        initLcovTarget = os.path.join(self.dir, 'coverage_data')
        initLcovSoureces = [self.prog]
        # Call builder initLcov().
        initLcov = self.env.InitLcov(initLcovTarget, initLcovSoureces)
        # Call builder RunLcov().
        target = "%s.cov" % target
        covTest = self.env.RunUnittest(target, self.prog)
        # Targets and sources for RunLcov() builder.
        metrics_dir = self.env['INSTALL_METRICS_DIR']
        coverage_dir = self.env.Dir(metrics_dir).Dir('coverage').Dir(self.name)
        runLcovTargets = os.path.join(coverage_dir.abspath, 'index.html')
        runLcovSources = [self.prog]
        # Call builder RunLcov().
        lcov = self.env.RunLcov(runLcovTargets, runLcovSources)
        # Create dependencies between targets.
        self.env.Depends(covTest, initLcov)
        self.env.Depends(lcov, covTest)
        # Create the target for coverage.
        cov = self.env.Alias('%s:coverage' % self.name[:-5], lcov)
        # Coverage can always be built.
        self.env.AlwaysBuild(cov)
        self.env.AlwaysBuild(covTest)
        return cov
