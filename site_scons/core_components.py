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
    This file contains the classes hierarchy for the components of the system.
"""


import os
import sys
import abc

import utils


headersFilter = ['*.h','*.hpp']
sourceFilters = ['*.c','*.cpp','*.cc']


class CyclicDependencieError(Exception):
    """
        An exception that represents a cycle in the dependence graph.
    """
    pass


class Component(abc.ABC):
    """
        This class represents a component.
        
        This is an abstract base class which contains the main interface for a 
        component.
    """
    
    #
    # Public attributes.
    # 
    # A string with the name of the component.
    name = None
    
    #
    # Private attributes.
    # 
    # The directory where the component lives (instance of SCons Dir class).
    _dir = None
    # The string representation of self._dir.
    _dir_path = None
    # A list with names of the components from which it depends.
    _dependencies = None
    # A list with the includes directories.
    _includes = None
    # A list of external includes directories.
    _external_includes = None
    # The environment of the component.
    _env = None
    # A list with the group of aliases to which the component belongs.
    _alias_groups = None
    # A reference to the graph of components.
    _component_graph = None
    # A boolean that tells if the component is linkable or not.
    _should_be_linked = False
    
    #
    # Special methods.
    #
      
    def __init__(self, graph, env, name, dir, deps, inc, ext_inc, aliases=None):
        self.name = name
        self._env = env.Clone()
        self._component_graph = graph
        self._dir = dir
        self._dir_path = dir.abspath
        self._dependencies = list(deps)
        self._includes = list(inc)
        self._external_includes = list(ext_inc)
        self._alias_groups = aliases if aliases is not None else []
    
    #
    # Public methods.
    #
    
    @abstractmethod
    def Process(self):
        """
            Description:
                This method describes how the component must be built and what 
                actions can be perform on it.
            Arguments:
                None. (If some subclass add arguments they must be optional).
            Exceptions:
                None. (If some subclass raise an exception it must be specified)
            Return:
                This method must return a reference to a builder, it can be an 
                instance of a Builder or an Alias.
        """
        return abc.NotImplemented
    
    def GetLibs(self):
        """
            Description:
                This method returns the libraries (and its paths) that should be 
                linked when the component needs to be built.
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
    
    def GetIncludePaths(self):
        """
            Description:
                This method looks for the include's paths of the component.
            Arguments:
                None.
            Exceptions:
                None.
            Return:
                A set of paths.
        """
        try:
            includes = self._GetIncludePaths(set(), [])[0]
        except CyclicDependencieError, error:
            msg = (' -> ').join(error[0])
            self.env.cerror('[error] A dependency cycle was found:\n  %s' % msg)
        return includes

    #
    # Private methods.
    #
    
    def _GetIncludePaths(self, include_paths, stack):
        """
            This is a recursive internal method used by the GetIncludePaths method.
        """
        if self.name in stack:
            # If the component name is within the stack then there is a cycle.
            stack.append(self.name)
            raise CyclicDependencieError(stack)
        else:
            # We add the component name to the stack.
            stack.append(self.name)
        if len(stack) == 1:
            # If we enter here is because we are looking for the includes of this
            # component.
            for path in self._includes:
                include_paths.add(path)
        else:
            # If we enter here is because someone else is looking for my includes.
            path = self.env.Dir('INSTALL_HEADERS_DIR').Dir(self.name).abspath
            include_paths.add(path)
        # We always add external includes.
        for path in self._external_includes:
            include_paths.add(path)
        # Look for the includes of its dependencies.
        for dependency in self._dependencies:
            component = self._component_graph.get(dependency)
            if component is not None:
                component._GetIncludePaths(include_paths, stack)
            else:
                self.env.cerror(
                    '[error] %s depends on %s which could not be found' % 
                    (self.name, dependency)
                )
        # We remove the component name from the stack.
        if self.name in stack:
            stack.pop()
    
    def _GetLibs(self, libs, libpaths, stack, depth):
        """
            This is a recursive internal method used by the GetLibs method.
        """
        if self.name in stack:
            # If the component name is within the stack then there is a cycle.
            stack.append(self.name)
            raise CyclicDependencieError(stack)
        else:
            # We add the component name to the stack.
            stack.append(self.name)
        if self._should_be_linked and depth > 0:
            libs.append((depth,self.name))
            # We add the directory where the library lives.
            if not self._dir_path in libpaths:
                libpaths.append(self._dir_path)
        # Check its dependencies.
        for dep in self._dependencies:
            c = self._component_graph.get(dep)
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


class ExternalComponent(Component):
    """
        This class represents an external component.
        
        External components are installed in the system rather than in the 
        fbuild install/ directory.
    """
    
    #
    # Special methods.
    #
    
    def __init__(self, graph, env, name, dir, deps, inc, linkable, aliases):
        Component.__init__(self, graph, env, name, dir, deps, [], inc, aliases)
        self._should_be_linked = linkable
    
    #
    # Public methods.
    #

    def Process(self):
        """
            This type of component no need to be built here.
        """
        pass


class HeaderOnlyComponent(Component):
    """
        This class represents a component which contains only header files.
    """
    
    #
    # Private attributes.
    #
    # The path to the project's directory into the fbuild projects/ folder.
    _project_dir = None
    
    #
    # Special methods.
    #
    
    def __init__(self, graph, env, name, dir, deps, ext_inc, aliases):
        Component.__init__(self, graph, env, name, dir, deps, [], ext_inc, aliases)
        self._project_dir = self.env.Dir('WS_DIR').Dir(self.name).abspath
    
    #
    # Public methods.
    #

    def Process(self, called_from_subclass=False):
        # Look for the sources of this component.
        filters = []
        filters.extend(headersFilter)
        filters.extend(sourceFilters)
        sources = utils.FilesFlatten(self.env, self.projDir, filters)
        # Create targets.
        self._CreateAstyleCheckTarget(sources)
        self._CreateAstyleTarget(sources)
        self._CreateCCCCTarget(sources)
        self._CreateClocTarget(sources)
        self._CreateCppcheckTarget(sources)
        self._CreateDocTarget()
        # If the component doesnt have external headers, we dont process it since
        # there is nothing to install
        if len(self.extInc) > 0:
            hLib = utils.RecursiveInstall(self.env, self.compDir, self.extInc, self.name, headersFilter)
            self.env.Alias(self.name, hLib, 'Install ' + self.name + ' headers')
            self.env.Clean(self.name, hLib)
            self.env.Alias('all:install', hLib, "Install all targets")
            for alias in self._alias_groups:
                self.env.Alias(alias, hLib, "Build group " + alias)
            return hLib
        # 
        # TODO: This must not be here. It must be in the 
        #       UnitTestComponent.Process(). This was for solving the problem 
        #       where the the coverage doesn't generate the report correctly.
        # 
        # Check if the coverage is needed.
        # 
        #if (utils.WasTargetInvoked('%s:jenkins' % self.name.split(':')[0]) or
        #   utils.WasTargetInvoked('%s:coverage' % self.name.split(':')[0])):
        #    gprofFlags = ['--coverage']
        #    self.env.Append(CXXFLAGS=gprofFlags, CFLAGS=gprofFlags, LINKFLAGS=gprofFlags)
    
    def GetSourcesFiles(self):
        """
            Description:
                This method does nothing for this class.
            Arguments:
                None.
            Exceptions:
                None.
            Return:
                An empty list.
        """
        return []
    
    def GetIncludeFiles (self):
        """
            Description:
                This method looks for the headers files of the component.
            Arguments:
                None.
            Exceptions:
                None.
            Return:
                A list of files.
        """
        include_files = []
        for include_dir in self._includes:
            hDir = os.path.join(self._project_dir, include_dir)
            if hDir.endswith('/.'):
                hDir = hDir.replace('/.','/')
            for p in [hDir+x for x in headersFilter]:
                include_files.extend(self.env.Glob(p))
        return include_files
    
    #
    # Private methods.
    #
    
    def _CreateCCCCTarget(self, sources):
        # The target is the cccc report file.
        target = self.env.Dir(self.env['INSTALL_REPORTS_DIR'])
        target = target.Dir(self.env['INSTALL_METRICS_DIR'])
        target = target.Dir('cccc').Dir(self.name)
        target = os.path.join(target.abspath, 'CCCCMainHTMLReport.html')
        # Create an instance of the RunCCCC() builder.
        cccc_builder = self.env.RunCCCC(target, sources)
        # cccc can always be build.
        self.env.AlwaysBuild(cccc_builder)
        # Create the alias.
        name = "%s:cccc" % self.name
        deps = [cccc_builder]
        msg = 'Run cccc for %s' % self.name
        self.env.Alias(name, deps, msg)
        # Return  the builder instance.
        return cccc_builder
    
    def _CreateClocTtarget(self, sources):
        # The target is the report file generated by cloc.
        target = self.env.Dir(self.env['INSTALL_REPORTS_DIR'])
        target = target.Dir(self.env['INSTALL_METRICS_DIR'])
        target = target.Dir('cloc').Dir(self.name)
        target = os.path.join(target.abspath, 'CLOCMainReport')
        # Create an instance of the RunCLOC() builder.
        cloc_builder = self.env.RunCLOC(target, sources)
        # cloc can always be build.
        self.env.AlwaysBuild(cloc)
        # Create the alias.
        name = "%s:cloc" % self.name
        deps = [cloc_builder]
        msg = 'Run cloc for %s' % self.name
        self.env.Alias(name, deps, msg)
        # Return the builder instance.
        return cloc_builder
    
    def _CreateCppcheckTarget(self, sources):
        # The target is the cppcheck report file.
        target = self.env.Dir(self.env['INSTALL_REPORTS_DIR'])
        target = target.Dir('cppcheck').Dir(self.name)
        target = os.path.join(target.abspath, 'CppcheckReport.txt')
        # Create an instance of the RunCppCheck() builder.
        cppcheck_builder = self.env.RunCppCheck(target, sources)
        # cppcheck can always be build.
        self.env.AlwaysBuild(cppcheck)
        # Create the alias.
        name = "%s:cppcheck" % self.name
        deps = [cppcheck_builder]
        mas = 'Run cppcheck for %s' % self.name
        self.env.Alias(name, deps, msg)
        # Return the builder instance.
        return cppcheck_builder
    
    def _CreateDocTarget(self):
        # The target is the directory where the documentation will be stored.
        target = self.env.Dir(self.env['INSTALL_DOC_DIR']).Dir(self.name)
        # The sources are:
        #   1) The doxyfile template.
        doxyfile = self.env.File(self.env.Dir('#').abspath+'/conf/doxygenTemplate')
        #   2) The SConscript of the project.
        #      We pass it the path to the SConscript file because we need the 
        #      path to the project directory but we only can put 'env.File' 
        #      objects as sources.
        sconscript = ('%s/SConscript' % self._dir_path).replace('/build/','/projects/')
        # Create an instance of the RunDoxygen() builder.
        doc_builder = self.env.RunDoxygen(target, [doxyfile,sconscript])
        self.env.Clean(doc, targetDocDir)
        # Create the alias.
        name = '%s:doc' % self.name
        deps = [doc_builder]
        msg = 'Generate documentation for %s' % self.name
        self.env.Alias(name, deps, msg)
        # Return the builder instance.
        return doc_builder
    
    def _CreateAstyleCheckTarget(self, sources):
        # The target is the .diff file.
        target = self.env.Dir(self.env['INSTALL_REPORTS_DIR'])
        target = target.Dir('astyle-check').Dir(name)
        target = os.path.join(target.abspath, 'AstyleCheckReport.diff')
        # Create an instance of the RunAStyleCheck() builder.
        astyle_check_builder = self.env.RunAStyleCheck(target, sources)
        # astyle-check can always be build.
        self.env.AlwaysBuild(astyle_check_builder)
        # Create the alias.
        name = '%s:astyle-check' % self.name
        deps = [astyle_check_builder]
        msg = "Checks if the project needs astyle."
        self.env.Alias(name, deps, msg)
        # Return the builder instance.
        return astyle_check_builder
    
    def _CreateAstyleTarget(self, sources):
        # We use the prject directory as the target.
        target = self.env.Dir(self.env['WS_DIR']).Dir(self.name)
        # Create an instance of the RunAStyle() builder.
        astyle_builder = self.env.RunAStyle(target, sources)
        # astyle can always be executed.
        self.env.AlwaysBuild(astyle_check_builder)
        # Create the alias.
        name = '%s:astyle' % self.name
        deps = [astyle_builder]
        msg = "Run astyle on %s" % self.name
        self.env.Alias(name, deps, msg)
        # Return the builder instance.
        return astyle_builder


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
        # Create list of sources and headers files
        self.src_files = []
        self.inc_files = self._GetIncludeFiles()
        for x in self.src:
            self.src_files.append(self.env.File(x))

    def Process(self):
        # Create the list of the 'sources' files.
        sources = self.src_files + self.inc_files
        # Create targets.
        self._CreateAstyleCheckTarget(sources)
        self._CreateAstyleTarget(sources)
        self._CreateCCCCTarget(sources)
        self._CreateClocTarget(sources)
        self._CreateCppcheckTarget(sources)
        self._CreateDocTarget()

    def GetIncludePaths(self):
        (incs, processedComponents) = self._GetIncludePaths([], 0)
        return incs


class ObjectComponent(SourcedComponent):
    
    def __init__(self, componentGraph, env, name, compDir, deps, inc, src, aliasGroups):
        SourcedComponent.__init__(self, componentGraph, env, name, compDir, deps, inc, [], src, aliasGroups)
        # A list of builders of the class Object().
        self.objects = []

    def Process(self):
        # Create the list of the 'sources' files.
        sources = self.src_files + self.inc_files
        # Create targets.
        self._CreateAstyleCheckTarget(sources)
        self._CreateAstyleTarget(sources)
        self._CreateCCCCTarget(sources)
        self._CreateClocTarget(sources)
        self._CreateCppcheckTarget(sources)
        self._CreateDocTarget()
        # If the objects are not compiled, we compile them.
        if not self.objects:
            # Get the list of include paths.
            incpaths = self.GetIncludePaths()
            # Get the list of libraries to link, and its directories.
            (libs,libpaths) = self.GetLibs()
            # Create an object from each file.
            for source in self.src_files:
                # Create the target for each file.
                target = source.abspath.split('.')[0]
                # Create an instance of the Object() builder.
                object_builder = self.env.Object(
                    target,
                    source,
                    CPPPATH = incpaths,
                    LIBPATH = libpaths,
                    LIBS = libs
                )
                # Add the builder to the list.
                self.objects.append(object_builder)
        return self.objects

    def FindSources(self):
        src_files = self.src_files
        for dependency in self._dependencies:
            dep_component = self._component_graph.get(dependency)
            if isinstance(dep_component, ObjectComponent):
                src_files.extend(dep_component.Process())
        return src_files


class StaticLibraryComponent(ObjectComponent):
    
    def __init__(self, componentGraph, env, name, compDir, deps, inc, extInc, src, aliasGroups):
        ObjectComponent.__init__(self, componentGraph, env, name, compDir, deps, inc, extInc, src, aliasGroups)
        self._should_be_linked = True

    def Process(self):
        # The target is the name of library to be created.
        target = os.path.join(self._dir_path, self.name)
        # Create the list of the 'sources' files.
        sources = self.src_files + self.inc_files
        # Create targets.
        self._CreateAstyleCheckTarget(sources)
        self._CreateAstyleTarget(sources)
        self._CreateCCCCTarget(sources)
        self._CreateClocTarget(sources)
        self._CreateCppcheckTarget(sources)
        self._CreateDocTarget()
        # Get include paths.
        includes = self.GetIncludePaths()
        # Create an instance of th StaticLibrary() builder.
        slib_builder = self.env.StaticLibrary(
            target,
            self.src_files,
            CPPPATH = includes
        )
        # Create an instance of the Install() builder.
        install_builder = self.env.Install(
            self.env['INSTALL_LIB_DIR'],
            slib_builder
        ) 
        # Create the aliases.
        name = self.name
        deps = [slib_builder]
        msg = "Build %s" % self.name
        self.env.Alias(name, deps, msg)
        self.env.Alias('all:build', slib_builder, "Build all targets")
        self.env.Alias('all:install', install_builder, "Install all targets")
        for alias in self._alias_groups:
            self.env.Alias(alias, install_builder, "Build group " + alias)
        # Return the instance builder.
        return slib_builder


class DynamicLibraryComponent(ObjectComponent):
    
    def __init__(self, componentGraph, env, name, compDir, deps, inc, extInc, src, aliasGroups):
        ObjectComponent.__init__(self, componentGraph, env, name, compDir, deps, inc, extInc, src, aliasGroups)
        self._should_be_linked = True

    def Process(self):
        # The target is the name of library to be created.
        target = os.path.join(self._dir_path, self.name)
        # Create the list of the 'sources' files.
        sources = self.src_files + self.inc_files
        # Create targets.
        self._CreateAstyleCheckTarget(sources)
        self._CreateAstyleTarget(sources)
        self._CreateCCCCTarget(sources)
        self._CreateClocTarget(sources)
        self._CreateCppcheckTarget(sources)
        self._CreateDocTarget()
        # Get include paths.
        includes = self.GetIncludePaths()
        # Get the libraries to link and tehir directories.
        (libs,libpaths) = self.GetLibs()
        # Create an instance of the SharedLibrary() builder.
        dlib_builder = self.env.SharedLibrary(
            target,
            self.src_files, 
            CPPPATH = incpaths, 
            LIBPATH = libpaths,
            LIBS = libs
        )
        # Create an instance of the Install() builder.
        install_builder = self.env.Install(
            self.env['INSTALL_LIB_DIR'], 
            dlib_builder
        )
        # Create the aliases.
        name = self.name
        deps = [install_builder]
        msg = "Build and install %s" % self.name
        self.env.Alias(name, deps, msg)
        self.env.Alias('all:build', dlib_builder, "Build all targets")
        self.env.Alias('all:install', install_builder, "Install all targets")
        for alias in self._alias_groups:
            self.env.Alias(alias, install_builder, "Build group " + alias)
        # Return the builder instance.
        return dlib_builder


class ProgramComponent(ObjectComponent):
    
    def __init__(self, componentGraph, env, name, compDir, deps, inc, src, aliasGroups):
        ObjectComponent.__init__(self, componentGraph, env, name, compDir, deps, inc, [], src, aliasGroups)

    def Process(self):
        # The target is the name of program to be created.
        target = os.path.join(self.env['INSTALL_LIB_DIR'], self.name)
        # Create the list of the 'sources' files.
        sources = self.src_files + self.inc_files
        # Create targets.
        self._CreateAstyleCheckTarget(sources)
        self._CreateAstyleTarget(sources)
        self._CreateCCCCTarget(sources)
        self._CreateClocTarget(sources)
        self._CreateCppcheckTarget(sources)
        self._CreateDocTarget()
        # Get include paths.
        includes = self.GetIncludePaths()
        # Get the libraries to link and their directories.
        (libs,libpaths) = self.GetLibs()
        # Create an instance of the Program() builder.
        program_builder = self.env.Program(
            target,
            self.FindSources(),
            CPPPATH = incpaths,
            LIBPATH = libpaths,
            LIBS = libs
        )
        # Create an instance of the Install() builder.
        install_builder = self.env.Install(
            self.env['INSTALL_BIN_DIR'],
            program_builder
        )
        # Create the aliases.
        self.env.Alias(
            self.name,
            install_builder,
            "Build and install %s" % self.name
        )
        self.env.Alias('all:build', program_builder, "Build all targets")
        self.env.Alias('all:install', install_builder, "Install all targets")
        for alias in self._alias_groups:
            self.env.Alias(alias, install_builder, "Build group " + alias)
        # Return the builder instance.
        return program_builder


class UnitTestComponent(ProgramComponent):
    
    def __init__(self, componentGraph, env, name, compDir, deps, inc, src, aliasGroups):
        ProgramComponent.__init__(self, componentGraph, env, name, compDir, deps, inc, src, aliasGroups)

    def Process(self):
        incpaths = self.GetIncludePaths()
        (libs,libpaths) = self.GetLibs()
        target = os.path.join(self._dir_path, self.name)
        self.prog = self.env.Program(target, self.FindSources(), CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        self.env.Alias(self.name, self.prog, "Build and install " + self.name)
        self.env.Alias('all:build', self.prog, "Build all targets")
        # Flags for gtest and gmock.
        CXXFLAGS = [f for f in self.env['CXXFLAGS'] if f not in ['-ansi', '-pedantic']]
        CXXFLAGS.append('-Wno-sign-compare')
        if not '-ggdb3' in CXXFLAGS:
            CXXFLAGS.append('-ggdb3')
        self.env.Replace(CXXFLAGS=CXXFLAGS, CFLAGS=CXXFLAGS)
        # Check if it needed to generate a test report.
        if (utils.wasTargetInvoked('%s:jenkins' % self.name.split(':')[0]) or 
           utils.wasTargetInvoked('%s:ready-to-commit' % self.name.split(':')[0])):
            gtest_report = self.env.Dir(self.env['INSTALL_REPORTS_DIR']).Dir('test').Dir(self.name[:-5])
            self.env.gtest_report = 'xml:%s/test-report.xml' % gtest_report.abspath
        # File to store the test results.
        target = os.path.join(self._dir_path, self.name + '.passed')
        tTest = self.env.RunUnittest(target, self.prog)
        # Check if the user want to run the tests anyway.
        if self.env.GetOption('forcerun'):
            self.env.AlwaysBuild(tTest)
        # Create the target for the test.
        self.env.Alias(self.name, tTest, "Run test for " + self.name)
        # Make the test depends from files in 'ref' dir.
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
        # Add dependence for ready to commit.
        self.env.Depends(self.ready_to_commit, tvalg)
        # Create alias for aliasGroups.
        for alias in self._alias_groups:
            self.env.Alias(alias, tTest, "Build group " + alias)

    def GetIncludePaths(self):
        includes = super(UnitTestComponent, self).GetIncludePaths()
        project = self._component_graph.get(self.name.split(':')[0])
        #adding current test dir
        filtered_includes = [self._dir_path, project.dir]
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
        if (utils.wasTargetInvoked('%s:jenkins' % self.name.split(':')[0]) or
            utils.wasTargetInvoked('%s:ready-to-commit' % self.name.split(':')[0])):
            report_dir = self.env['INSTALL_REPORTS_DIR']
            vdir = self.env.Dir(report_dir).Dir('valgrind').Dir(self.name[:-5])
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
        project = self._component_graph.get(self.name.split(':')[0])
        self.env['PROJECT_DIR'] = project.dir        
        # Targets and sources for builder InitLcov.
        initLcovTarget = os.path.join(self._dir_path, 'coverage_data')
        initLcovSoureces = [self.prog]
        # Call builder initLcov().
        initLcov = self.env.InitLcov(initLcovTarget, initLcovSoureces)
        # Call builder RunLcov().
        target = "%s.cov" % target
        covTest = self.env.RunUnittest(target, self.prog)
        # Make the test depends from files in 'ref' dir.
        for refFile in utils.FindFiles(self.env, self.compDir.Dir('ref')):
            self.env.Depends(covTest, refFile)
        # Targets and sources for RunLcov() builder.
        reports_dir = self.env['INSTALL_REPORTS_DIR']
        coverage_dir = self.env.Dir(reports_dir).Dir('coverage').Dir(self.name)
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

    def _CreateJenkinsTarget(self):
        # Create the target for jenkins.
        name = self.name.split(':')[0]
        self.jenkins_target = self.env.Alias('%s:jenkins' % name, None, '')
        self.env.AlwaysBuild(self.jenkins_target)

    def _create_ready_to_commit_target(self):
        self.ready_to_commit = self.env.RunReadyToCommit(self.name, None)
        # Create an alias for ready-to-commit.
        self.env.Alias('%s:ready-to-commit' % self.name.split(':')[0], self.ready_to_commit, '')
        self.env.AlwaysBuild(self.ready_to_commit)
        
    # 
    # ============> This is for jenkis. <=====================
    #
    # Check if we need to create an xml report.
    #
    #if utils.wasTargetInvoked('%s:jenkins' % self.name.split(':')[0]):
    #    self.env.Replace(CLOC_OUTPUT_FORMAT='xml')
    #self.env.Depends(self.jenkins_target,cloc)
