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
import abc

from SCons import Node
from SCons.Script.SConscript import SConsEnvironment
from componentsgraph import COMPONENT_GRAPH
import utils
import fbuild_exceptions



HEADERS_FILTER = ['*.h', '*.hpp']
SOURCES_FILTER = ['*.c', '*.cpp', '*.cc']

class ComponentMeta(abc.ABCMeta):

    """
    Registers Components into the SConsEnvironment
    """
    
    def __init__(cls, name, bases, attrs):
        # cls._component_graph.update
        super(ComponentMeta, cls).__init__(name, bases, attrs)
        aliases = attrs.get('_alias')
        template = 'Create{}'.format
        
        def component_factory(self, *args, **kwargs):
            COMPONENT_GRAPH.update(
                {name: cls(COMPONENT_GRAPH, self, *args, **kwargs)})
        
        if isinstance(aliases, tuple):
            [setattr(SConsEnvironment, template(a), component_factory) for a in aliases]
        
        setattr(SConsEnvironment, template(name), component_factory)


class Component(object):
    """
        This class represents a component in the component graph.

        This is an abstract base class which contains the main interface for
        a component.
    """

    # Make this class an abstract class.
    __metaclass__ = ComponentMeta

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
    # A list with names of the components from which it depends.
    _dependencies = None
    # A list with the includes directories (instances of SCons Dir class).
    _includes = None
    # A list with the path of the include directories.
    _include_paths = None
    # A list of external includes directories (instances of SCons Dir class).
    _external_includes = None
    # A list with the libraries that need to be linked for build this
    # component.
    _libs = None
    # A list with the path to the libraries that need to be linked for build
    # this component.
    _libpaths = None
    # The list of objects file to be linked when build this component.
    _object_files = None
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

    def __init__(self, env, name, dir, deps, inc, ext_inc, als=None):
        # Check consistency for some types.
        self.name = name
        self._env = env.Clone()
        self._dir = dir
        self._dependencies = deps
        self._includes = utils.format_argument(inc)
        self._external_includes = utils.format_argument(ext_inc)
        self._alias_groups = als if als is not None else []
        self._env._USE_MOCKO = 'mocko' in deps
        

    #
    # Public methods.
    #

    @abc.abstractmethod
    def Process(self):
        """
            Description:
                This method describes how the component must be built and
                what actions can be perform on it.
            Arguments:
                None. (If some subclass add arguments they must be optional).
            Exceptions:
                None. (If some subclass raise an exception it must be
                specified here)
            Return:
                This method must return a reference to a builder (it can be
                an instance of a Builder or an Alias) or None if the
                component does not need to be built.
        """
        return NotImplemented

    def GetLibs(self):
        """
            Description:
                This method returns the libraries (and its paths) that should
                be linked when the component needs to be built.
            Arguments:
                None.
            Exceptions:
                None.
            Return:
                A tuple instance of the form (libs,libpaths) where 'libs' is
                the list of the libraries and 'libpaths' the list of its paths.
        """
        if self._libs is not None and self._libpaths is not None:
            return (self._libs, self._libpaths)
        else:
            self._libs = []
            self._libpaths = []
        # Append some strandars paths to this variable.
        self._libpaths.append(self._env['INSTALL_LIB_DIR'])
        # Look for the libs and its paths.
        try:
            self._GetLibs(self._libs, self._libpaths, [], 0)
        except fbuild_exceptions.CircularDependencyError, error:
            msg = (' -> ').join(error[0])
            self._env.cerror('[error] A dependency cycle was found:\n  %s' % msg)
        # Remember:
        #   t[0]  ->  depth.
        #   t[1]  ->  name.
        # This function tells if the tuple depth (t[0]) is the maximum in
        # self._libs.
        IsMax = lambda t: len([x for x in self._libs if (x[1] == t[1]) and (x[0] > t[0])]) == 0
        # This function tells if the tuple name (t[1]) is unique in
        # self._libs.
        Unique = lambda t: len([x for x in self._libs if x[1] == t[1]]) == 1
        # Remove from the list the duplicated names.
        aux = [t for t in self._libs if Unique(t) or IsMax(t)]
        aux = utils.RemoveDuplicates(aux)
        aux.sort()
        # Create the self._libs list.
        self._libs = [t[1] for t in aux]
        return (self._libs, self._libpaths)

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
        if self._include_paths is not None:
            return list(self._include_paths)
        else:
            self._include_paths = set()
        try:
            self._GetIncludePaths(self._include_paths, [])
        except fbuild_exceptions.CircularDependencyError, error:
            msg = (' -> ').join(error[0])
            self._env.cerror('[error] A dependency cycle was found:\n  %s' % msg)
        return list(self._include_paths)

    def GetIncludeFiles(self):
        """
            Description:
                This method looks for the headers files of the component.
            Arguments:
                None.
            Exceptions:
                None.
            Return:
                A list of files. Each file is an instance of the SCons File
                class.
        """
        return []

    def GetSourcesFiles(self):
        """
            Description:
                This method return a list with source files of the component.
            Arguments:
                None.
            Exceptions:
                None.
            Return:
                A list with the source files, each element is an instance
                of the SCons File class.
        """
        return []

    def GetObjectsFiles(self):
        """
            Description:
                This method looks for the objects files that this component
                needs to be built.
            Arguments:
                None.
            Exceptions:
                None.
            Return:
                A list with instance of the SCons Object() class.
        """
        if self._object_files is not None:
            return self._object_files
        else:
            self._object_files = []
        try:
            self._GetObjectsFiles(self._object_files, [])
        except fbuild_exceptions.CircularDependencyError, error:
            msg = (' -> ').join(error[0])
            self._env.cerror('[error] A dependency cycle was found:\n  %s' % msg)
        return self._object_files

    # Private methods.
    #

    def _GetObjectsFiles(self, object_files, stack):
        """
            This is a recursive internal method used by the GetObjectsFiles
            method.
        """
        if self.name in stack:
            # If the component name is within the stack then there is a
            # cycle.
            stack.append(self.name)
            raise fbuild_exceptions.CircularDependencyError(stack)
        else:
            # We add the component name to the stack.
            stack.append(self.name)
        if ((len(stack) == 1 and isinstance(self,ObjectComponent)) or
            (type(self) == ObjectComponent)):
            self._CreateObjectFiles()
            object_files.extend(self._objects)
        for dependency in self._dependencies:
            try:
                component = self._component_graph[dependency]
            except (IndexError, KeyError):
                self._env.cerror(
                    '[error] %s depends on %s which could not be found' %
                    (self.name, dependency)
                )
            else:
                component._GetObjectsFiles(object_files, stack)
        # We remove the component name from the stack.
        if self.name in stack:
            stack.pop()

    def _GetIncludePaths(self, include_paths, stack):
        """
            This is a recursive internal method used by the GetIncludePaths
            method.
        """
        if self.name in stack:
            # If the component name is within the stack then there is a
            # cycle.
            stack.append(self.name)
            raise fbuild_exceptions.CircularDependencyError(stack)
        else:
            # We add the component name to the stack.
            stack.append(self.name)
        if len(stack) == 1:
            # If we're here is because we are looking for the include of this
            # component.
            if isinstance(self, UnitTestComponent):
                # If this is a UnitTestComponent we need the include directories
                # from its component.
                component = self._component_graph.get(self._project_name)
                for path in component._includes:
                    include_paths.add(path)
            else:
                # For any other component we use the _includes list.
                for path in self._includes:
                    include_paths.add(path)
            # We also add the install/include/ and the build/project/ directories.
            include_paths.add(self._env.Dir('$INSTALL_HEADERS_DIR').abspath)
            include_paths.add(self._dir.abspath)
        else:
            # If we're here is because we're looking for the include of the
            # dependency of a component.
            # 'self' can not be a UnitTestComponent. Because a
            # 'UnitTestComponent should never be a dependency of other
            # component.
            assert(not isinstance(self, UnitTestComponent))
            if isinstance(self, ExternalComponent):
                for path in self._includes:
                    include_paths.add(path)
            else:
                path = self._env.Dir('$INSTALL_HEADERS_DIR')
                path = path.Dir(self.name).abspath
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
                self._env.cerror(
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
            raise fbuild_exceptions.CircularDependencyError(stack)
        else:
            # We add the component name to the stack.
            stack.append(self.name)
        if self._should_be_linked and depth > 0:
            libs.append((depth, self.name))
            # We add the directory where the library lives.
            if not self._dir.abspath in libpaths:
                libpaths.append(self._dir.abspath)
        # Check its dependencies.
        for dep in self._dependencies:
            c = self._component_graph.get(dep)
            if c is None:
                self._env.cerror(
                    '[error] %s depends on %s which could not be found' %
                    (self.name, dep)
                )
            else:
                c._GetLibs(libs, libpaths, stack, depth + 1)
        # We remove the component name from the stack.
        if self.name in stack:
            stack.pop()

    def _CreateInstallerBuilder(self, binaries):
        """
            This method creates an installer builder.
        """
        if isinstance(self, ProgramComponent):
            binaries_dir = self._env.Dir('$INSTALL_BIN_DIR')
        else:
            binaries_dir = self._env.Dir('$INSTALL_LIB_DIR')
        inc_installer = utils.RecursiveInstall(
            self._env,
            self._dir,
            self._includes,
            self.name,
            HEADERS_FILTER
        )
        bin_installer = self._env.Install(binaries_dir, binaries)
        installers = bin_installer + inc_installer
        # Create the alias for install the component.
        self._env.Alias(self.name, installers, 'Install %s.' % self.name)
        return installers

    def _CreateGroupAliases(self):
        """
            This method creates the aliases for the group.
        """
        for alias in self._alias_groups:
            self._env.Alias(alias, None, "Build group %s" % alias)


class ExternalComponent(Component):
    """
        This class represents an external component.

        External components are installed in the system rather than in the
        fbuild install/ directory.
    """

    #
    # Special methods.
    #

    def __init__(self, graph, env, name, dir, deps, inc, linkable, als=None):
        import ipdb; ipdb.set_trace()
        super(ExternalComponent, self).__init__(graph, env, name, dir, deps, inc, [], als)
        self._should_be_linked = linkable

    #
    # Public methods.
    #

    def Process(self):
        """
            This type of component no need to be built here.
        """
        return []


class HeaderOnlyComponent(Component):
    """
        This class represents a header only component.

        This type of component does not have sources files, it contains only
        header files.
    """

    #
    # Private attributes.
    #
    # The path to the project's directory into the fbuild projects/ folder.
    # (instance of SCons Dir class).
    _project_dir = None
    # A list with the header files (instance of SCons File class). Never use
    # this attribute directly, always use the method GetIncludeFiles().
    _header_file_list = None
    # A dictionary with the builder of the component that can have a target
    # like 'project:target'.
    _builders = None

    #
    # Special methods.
    #

    def __init__(self, graph, env, name, dir, deps, inc, als=None):
        Component.__init__(self, graph, env, name, dir, deps, inc, [], als)
        self._project_dir = self._env.Dir('WS_DIR').Dir(self.name)
        self._builders = {  # Maintain alphabetical order.
            'astyle': None,
            'astyle-check': None,
            'cccc': None,
            'cloc': None,
            'coverage': None,
            'cppcheck': None,
            'doc': None,
            'install': None,
            'jenkins': None,
            'ready-to-commit': None,
            'test': None,
            'valgrind': None
        }

    #
    # Public methods.
    #

    def Process(self):
        """
            Description:
                This method creates the targets of the actions that can be
                applied to this component.
            Arguments:
                None.
            Exceptions:
                None.
            Return:
                An instance of a builder which tell how to install the
                component.
        """
        # Check if the component was already processed.
        if self._builders['install'] is not None:
            return self._builders['install']
        # Look for the sources of this component.
        headers = self.GetIncludeFiles()
        # Create targets.
        self._CreateAstyleCheckTarget(headers)
        self._CreateAstyleTarget(headers)
        self._CreateCCCCTarget(headers)
        self._CreateClocTarget(headers)
        self._CreateCppcheckTarget(headers)
        self._CreateDocTarget()
        # Create the installer.
        installer = self._CreateInstallerBuilder([])
        # Create the alias group.
        self._CreateGroupAliases()
        # Set the installer into the builders dictionary.
        self._builders['install'] = installer
        return installer

    def GetIncludeFiles(self):
        """
            Description:
                This method looks for the headers files of the component.
            Arguments:
                None.
            Exceptions:
                None.
            Return:
                A list of files. Each file is an instance of the SCons File
                class.
        """
        # If the files were already calculate we just return them.
        if self._header_file_list is not None:
            return self._header_file_list
        # Otherwise we look for them.
        self._header_file_list = []
        # Look for the files in each include directory.
        for include_dir in self._includes:
            files = utils.FindFiles(self._env, include_dir, HEADERS_FILTER)
            self._header_file_list.extend(files)
        return self._header_file_list

    #
    # Private methods.
    #

    def _CreateDocTarget(self):
        if self._builders['doc'] is not None:
            return self._builders['doc']
        # The target is the directory where the documentation will be stored.
        target = self._env.Dir(self._env['INSTALL_DOC_DIR']).Dir(self.name)
        # The sources are:
        #   1) The doxyfile template.
        doxyfile = self._env.File(
            self._env.Dir('#').abspath + '/conf/doxygenTemplate'
        )
        #   2) The SConscript of the project.
        #      We pass it the path to the SConscript file because we need the
        #      path to the project directory but we only can put 'env.File'
        #      objects as sources.
        sconscript = ('%s/SConscript' % self._dir.abspath).replace(
            '/build/',
            '/projects/'
        )
        # Create an instance of the RunDoxygen() builder.
        doc_builder = self._env.RunDoxygen(target, [doxyfile, sconscript])
        # Create the alias.
        name = '%s:doc' % self.name
        deps = [doc_builder]
        msg = 'Generate documentation for %s' % self.name
        self._env.Alias(name, deps, msg)
        # Save the builder into the builder dictionary.
        self._builders['doc'] = doc_builder
        # Return the builder instance.
        return doc_builder

    def _CreateCCCCTarget(self, sources):
        if self._builders['cccc'] is not None:
            return self._builders['cccc']
        # The target is the cccc report file.
        target = self._env.Dir(self._env['INSTALL_REPORTS_DIR'])
        target = target.Dir(self._env['INSTALL_METRICS_DIR'])
        target = target.Dir('cccc').Dir(self.name)
        target = os.path.join(target.abspath, 'CCCCMainHTMLReport.html')
        # Create an instance of the RunCCCC() builder.
        cccc_builder = self._env.RunCCCC(target, sources)
        # cccc can always be build.
        self._env.AlwaysBuild(cccc_builder)
        # Create the alias.
        name = "%s:cccc" % self.name
        deps = [cccc_builder]
        msg = 'Run cccc for %s' % self.name
        self._env.Alias(name, deps, msg)
        # Save the builder into the builder dictionary.
        self._builders['cccc'] = cccc_builder
        # Return  the builder instance.
        return cccc_builder

    def _CreateClocTarget(self, sources):
        if self._builders['cloc'] is not None:
            return self._builders['cloc']
        # The target is the report file generated by cloc.
        target = self._env.Dir('$INSTALL_METRICS_DIR')
        target = target.Dir('cloc').Dir(self.name)
        target = os.path.join(target.abspath, 'CLOCMainReport')
        # Create an instance of the RunCLOC() builder.
        cloc_builder = self._env.RunCLOC(target, sources)
        # cloc can always be build.
        self._env.AlwaysBuild(cloc_builder)
        # Create the alias.
        name = "%s:cloc" % self.name
        deps = [cloc_builder]
        msg = 'Run cloc for %s' % self.name
        self._env.Alias(name, deps, msg)
        # Save the builder into the builder dictionary.
        self._builders['cloc'] = cloc_builder
        # Return the builder instance.
        return cloc_builder

    def _CreateCppcheckTarget(self, sources):
        if self._builders['cppcheck'] is not None:
            return self._builders['cppcheck']
        self._env['CPPCHECK_OPTIONS'] += [
            '-I{}'.format(x) for x in self.GetIncludePaths()
        ]
        # The target is the cppcheck report file.
        
        target = self._env.Dir(self._env['INSTALL_REPORTS_DIR'])
        target = target.Dir('cppcheck').Dir(self.name)
        target = os.path.join(target.abspath, 'CppcheckReport')
        # Create an instance of the RunCppCheck() builder.
        cppcheck_builder = self._env.RunCppCheck(target, sources)
        # cppcheck can always be build.
        self._env.AlwaysBuild(cppcheck_builder)
        # Create the alias.
        name = "%s:cppcheck" % self.name
        deps = [cppcheck_builder]
        msg = 'Run cppcheck for %s' % self.name
        self._env.Alias(name, deps, msg)
        # Save the builder into the builder dictionary.
        self._builders['cppcheck'] = cppcheck_builder
        # Return the builder instance.
        return cppcheck_builder

    def _CreateAstyleCheckTarget(self, sources):
        if self._builders['astyle-check'] is not None:
            return self._builders['astyle-check']
        # The target is the .diff file.
        target = self._env.Dir(self._env['INSTALL_REPORTS_DIR'])
        target = target.Dir('astyle-check').Dir(self.name)
        target = target.File('AstyleCheckReport.diff')
        # Create an instance of the RunAStyleCheck() builder.
        astyle_check_builder = self._env.RunAStyleCheck(target, sources)
        # astyle-check can always be build.
        self._env.AlwaysBuild(astyle_check_builder)
        # Create the alias.
        name = '%s:astyle-check' % self.name
        deps = [astyle_check_builder]
        msg = "Checks if the project needs astyle."
        self._env.Alias(name, deps, msg)
        # Save the builder into the builder dictionary.
        self._builders['astyle-check'] = astyle_check_builder
        # Return the builder instance.
        return astyle_check_builder

    def _CreateAstyleTarget(self, sources):
        if self._builders['astyle'] is not None:
            return self._builders['astyle']
        # We use the prject directory as the target.
        target = self._env.Dir(self._env['WS_DIR']).Dir(self.name)
        # Create an instance of the RunAStyle() builder.
        astyle_builder = self._env.RunAStyle(target, sources)
        # astyle can always be executed.
        self._env.AlwaysBuild(astyle_builder)
        # Create the alias.
        name = '%s:astyle' % self.name
        deps = [astyle_builder]
        msg = "Run astyle on %s" % self.name
        self._env.Alias(name, deps, msg)
        # Save the builder into the builder dictionary.
        self._builders['astyle'] = astyle_builder
        # Return the builder instance.
        return astyle_builder


class SourcedComponent(HeaderOnlyComponent):
    """
        This class represents a sourced component.

        This type of component can have sources and headers files.
    """

    #
    # Private attributes.
    #
    # A list with the sources files (instances of the SCons File class).
    # Never use this attribute directly, use the GetSourcesFiles() method.
    _sources_file_list = None

    #
    # Special methods.
    #

    def __init__(self, graph, env, name, dir, deps, inc, ext_inc, src, als=None):
        HeaderOnlyComponent.__init__(self, graph, env, name, dir, deps, ext_inc, als)
        # Because HeaderOnlyComponent doesn't have includes.
        self._includes = utils.format_argument(inc)
        # Check the 'src' argument.
        if not src:
            msg = "[ERROR] %s: No sources were specified for a" % self.name
            self._env.cerror("%s SourcedComponent object." % msg)
            raise ValueError("No sources were specified for a SourcedComponent object.")
        # Initialize the source files.
        self._InitSourcesFileList(src)

    #
    # Public methods.
    #

    def Process(self):
        """
            Description:
                This method creates the targets of the actions that can be
                applied to this component.
            Arguments:
                None.
            Exceptions:
                None.
            Return:
                None. (A sourced component can't be built nor installed.)
        """
        # Check if the component was already processed.
        if self._builders['install'] is None:
            # Create the list of the 'sources' files.
            sources = self.GetSourcesFiles() + self.GetIncludeFiles()
            # Create targets.
            self._CreateAstyleCheckTarget(sources)
            self._CreateAstyleTarget(sources)
            self._CreateCCCCTarget(sources)
            self._CreateClocTarget(sources)
            self._CreateCppcheckTarget(sources)
            self._CreateDocTarget()
            self._builders['install'] = True
        # We retuen an empty list because a sourced has nothing to install.
        return []

    def GetSourcesFiles(self):
        """
            Description:
                This method return a list with source files of the component.
            Arguments:
                None.
            Exceptions:
                None.
            Return:
                A list with the source files, each element is an instance of
                the SCons File class.
        """
        # A sourced component must have at least one element.
        assert(len(self._sources_file_list) > 0)
        return self._sources_file_list

    #
    # Private methods.
    #

    def _InitSourcesFileList(self, src):
        """
            This is an internal method that initialize the list of sources
            files.
        """
        # This method must be called only once.
        assert(self._sources_file_list is None)
        # Create the list.
        self._sources_file_list = []
        self._InitSourcesFileRec(self._sources_file_list, src)

    def _InitSourcesFileRec(self, files, src):
        """
            This is a private method used by _InitSourcesFileList().
            It looks for the file recursively.
        """
        if isinstance(src, Node.FS.Dir):
            # If it's a Dir we read the files it contains.
            files.extend(utils.FindFiles(src, SOURCES_FILTER))
        elif isinstance(src, Node.FS.File):
            # If it's a File, we just add it.
            files.append(src)
        elif isinstance(src, str):
            # If it's a string it must be a file.
            files.append(self._env.File(src))
        else:
            # It must be an iterable object.
            for source in src:
                self._InitSourcesFileRec(files, source)


class ObjectComponent(SourcedComponent):
    """
        This class represents a set of objects files, from which other
        component can depend to be built.
    """

    #
    # Private attributes.
    #
    # A list with the object files (instances of the SCons Object() class).
    _objects = None

    #
    # Special methods.
    #

    def __init__(self, graph, env, name, dir, deps, inc, src, als=None):
        super(ObjectComponent, self).__init__(graph, env, name, dir, deps, inc, [], src, als)
        # A list of builders of the class Object().
        self._objects = []

    #
    # Public methods.
    #

    def Process(self):
        # Check if the component was already processed.
        if self._builders['install'] is not None:
            return self._builders['install']
        # Create the list of the 'sources' files.
        sources = self.GetSourcesFiles() + self.GetIncludeFiles()
        # Create targets.
        self._CreateAstyleCheckTarget(sources)
        self._CreateAstyleTarget(sources)
        self._CreateCCCCTarget(sources)
        self._CreateClocTarget(sources)
        self._CreateCppcheckTarget(sources)
        self._CreateDocTarget()
        # Initialize the object file list.
        self._CreateObjectFiles()
        # Create the installer.
        installer = self._CreateInstallerBuilder(self._objects)
        # Create the group aliases.
        self._CreateGroupAliases()
        self._builders['install'] = installer
        return installer

    #
    # Private methods.
    #

    def _CreateObjectFiles(self):
        """
            Initialize the list of object files.
        """
        if not self._objects:
            for source in self.GetSourcesFiles():
                self._objects.append(self._CreateObjectBuilder(source))

    def _CreateObjectBuilder(self, source):
        """
            This is a private method that takes a file source and return an
            instance of the SCons Object() builder class.
        """
        # Get the list of include paths.
        include_paths = self.GetIncludePaths()
        # Get the list of libraries to link, and its directories.
        (libs, libpaths) = self.GetLibs()
        # Create the target for each file.
        target = source.abspath.split('.')[0]
        # Create an instance of the Object() builder.
        object_builder = self._env.Object(
            target,
            source,
            CPPPATH=include_paths,
            LIBPATH=libpaths,
            LIBS=libs
        )
        # Return the builder instance.
        return object_builder


class StaticLibraryComponent(ObjectComponent):
    """
        This class represents a static library component.
    """

    #
    # Special methods.
    #

    def __init__(self, graph, env, name, dir, deps, inc, ext_inc, src, als=None):
        super(StaticLibraryComponent, self).__init__(graph, env, name, dir, deps, inc, src, als)
        self._should_be_linked = True

    #
    # Public methods.
    #

    def Process(self):
        # Check if the component was already processed.
        if self._builders['install'] is not None:
            return self._builders['install']
        # The target is the name of library to be created.
        target = os.path.join(self._dir.abspath, self.name)
        # Create the list of the 'sources' files.
        sources = self.GetSourcesFiles() + self.GetIncludeFiles()
        # Create targets.
        self._CreateAstyleCheckTarget(sources)
        self._CreateAstyleTarget(sources)
        self._CreateCCCCTarget(sources)
        self._CreateClocTarget(sources)
        self._CreateCppcheckTarget(sources)
        self._CreateDocTarget()
        # Create a static library builder.
        slib_builder = self._CreateStaticLibraryBuilder(target)
        # Create an installer builders.
        installer = self._CreateInstallerBuilder([slib_builder])
        # Create the group aliases.
        self._CreateGroupAliases()
        self._builders['install'] = installer
        return installer

    #
    # Private methods.
    #

    def _CreateStaticLibraryBuilder(self, target):
        # Get include paths.
        includes = self.GetIncludePaths()
        # Create an instance of th StaticLibrary() builder.
        slib_builder = self._env.StaticLibrary(
            target,
            self.GetObjectsFiles(),
            CPPPATH=includes
        )
        # Create the all:buil alias.
        self._env.Alias('all:build', slib_builder, "Build all targets")
        return slib_builder


class DynamicLibraryComponent(ObjectComponent):
    """
        This class represents a shared library component.
    """

    #
    # Special methods.
    #

    def __init__(self, graph, env, name, dir, deps, inc, ext_inc, src, als=None):
        super(DynamicLibraryComponent, self).__init__(graph, env, name, dir, deps, inc, src, als)
        self._should_be_linked = True

    #
    # Public methods.
    #

    def Process(self):
        # Check if the component was already processed.
        if self._builders['install'] is not None:
            return self._builders['install']
        # The target is the name of library to be created.
        target = os.path.join(self._dir.abspath, self.name)
        # Create the list of the 'sources' files.
        sources = self.GetSourcesFiles() + self.GetIncludeFiles()
        # Create targets.
        self._CreateAstyleCheckTarget(sources)
        self._CreateAstyleTarget(sources)
        self._CreateCCCCTarget(sources)
        self._CreateClocTarget(sources)
        self._CreateCppcheckTarget(sources)
        self._CreateDocTarget()
        # Create the shared library builder.
        dlib_builder = self._CreateSharedLibraryBuilder(target)
        # Create the installer builder.
        installer = self._CreateInstallerBuilder([dlib_builder])
        self._builders['install'] = installer
        return installer

    #
    # Private methods.
    #

    def _CreateSharedLibraryBuilder(self, target):
        # Get include paths.
        includes = self.GetIncludePaths()
        # Get the libraries to link and tehir directories.
        (libs, libpaths) = self.GetLibs()
        # Create an instance of the SharedLibrary() builder.
        dlib_builder = self._env.SharedLibrary(
            target,
            self.GetSourcesFiles(),
            CPPPATH=includes,
            LIBPATH=libpaths,
            LIBS=libs
        )
        # Create the all:build alias.
        self._env.Alias('all:build', dlib_builder, "Build all targets")
        return dlib_builder


class ProgramComponent(ObjectComponent):
    """
        This class represents a program (executable) component.
    """

    #
    # Special methods.
    #

    def __init__(self, graph, env, name, dir, deps, inc, src, als=None):
        super(ProgramComponent).__init__(self, graph, env, name, dir, deps, inc, src, als)

    #
    # Public methods.
    #

    def Process(self):
        # Check if the component was already processed.
        if self._builders['install'] is not None:
            return self._builders['install']
        # The target is the name of program to be created.
        target = os.path.join(self._env['BUILD_DIR'], self.name)
        target = os.path.join(target, 'bin')
        target = os.path.join(target, self.name)
        # Create the list of the 'sources' files.
        sources = self.GetSourcesFiles() + self.GetIncludeFiles()
        # Create targets.
        self._CreateAstyleCheckTarget(sources)
        self._CreateAstyleTarget(sources)
        self._CreateCCCCTarget(sources)
        self._CreateClocTarget(sources)
        self._CreateCppcheckTarget(sources)
        self._CreateDocTarget()
        # Create the program builder.
        program_builder = self._CreateProgramBuilder(target)
        # Create an instance of the Install() builder.
        installer = self._CreateInstallerBuilder([program_builder])
        # Create the group aliases.
        self._CreateGroupAliases()
        self._builders['install'] = installer
        return installer

    #
    # Private methods.
    #

    def _CreateProgramBuilder(self, target, sources=None):
        sources = sources if sources is not None else []
        # Get include paths.
        includes = self.GetIncludePaths()
        # Get the libraries to link and their directories.
        (libs, libpaths) = self.GetLibs()
        # Get the objects files.
        sources.extend(self.GetObjectsFiles())
        # Create an instance of the Program() builder.
        program_builder = self._env.Program(
            target,
            sources,
            CPPPATH=includes,
            LIBPATH=libpaths,
            LIBS=libs
        )
        # Craete the all:build alias.
        self._env.Alias('all:build', program_builder, "Build all targets")
        return program_builder


class UnitTestComponent(ProgramComponent):
    """
        This class represents a test component.
    """

    #
    # Private attributes.
    #
    # The name of the project from which the test component depends.
    _project_name = None
    _alias = ('Program', )

    #
    # Special methods.
    #

    def __init__(self, env, name, dir, deps, inc, src, als):
        test_name = '%s@test' % name
        self._project_name = name
        if name not in deps:
            deps.append(name)
        else:
            msg = '[WARNING] %s: In test SConscript - Project added as a dependency of its test.' % name
            env.Cprint(msg, 'yellow')
        super(UnitTestComponent, self).__init__(env, test_name, dir, deps, inc, src, als=als)

    #
    # Public methods.
    #

    def Process(self):
        # Check if the component was already processed.
        if self._builders['install'] is not None:
            return self._builders['install']
        # Create the target.
        target = os.path.join(self._dir.abspath, '%s_test' % self._project_name)
        # File to store the test results.
        passed_file_name = '%s.passed' % self._project_name
        run_test_target = os.path.join(self._dir.abspath, passed_file_name)
        # Check for the flags we need to set in the environment.
        flags = self._CheckForFlags()
        # Check for use 'mocko'.
        sources = []
        if self._env._USE_MOCKO:
            self._UseMocko(sources)
        # Create the builder that creates the test executable.
        program_builder = self._CreateProgramBuilder(target, sources)
        # Creante an instance of the RunUnittest() builder.
        run_test_builder = self._env.RunUnittest(run_test_target, program_builder)
        # Check if the user want to run the tests anyway.
        if self._env.GetOption('forcerun'):
            self._env.AlwaysBuild(run_test_builder)
        # Make the execution of test depends from files in 'ref' dir.
        for refFile in utils.FindFiles(self._env, self._dir.Dir('ref')):
            self._env.Depends(program_builder, refFile)
        # Create the alias for 'project:test'.
        name = '%s:test' % self._project_name
        deps = [run_test_builder]
        msg = "Run test for %s" % self._project_name
        self._env.Alias(name, deps, msg)
        # Create alias for 'all:test'.
        self._env.Alias('all:test', run_test_builder, "Run all tests")
        # Create alias for aliasGroups.
        self._CreateGroupAliases()
        # Create targets.
        self._CreateValgrindTarget(program_builder)
        self._CreateCoverageTarget(run_test_target, program_builder)
        self._CreateJenkinsTarget(flags, run_test_target, program_builder)
        self._CreateReadyToCommitTtarget(flags, run_test_target, program_builder)
        self._builders['install'] = run_test_builder
        # Return the builder that execute the test.
        return run_test_builder

    def _CheckForFlags(self):
        # Get the component of the project.
        project_component = self._component_graph.get(self._project_name)
        # Flags for check the calling targets.
        jenkins = utils.WasTargetInvoked('%s:jenkins' % self._project_name)
        coverage = utils.WasTargetInvoked('%s:coverage' % self._project_name)
        rtc = (utils.WasTargetInvoked('%s:rtc' % self._project_name) or
              utils.WasTargetInvoked('%s:ready-to-commit' % self._project_name))
        # Create the dictionary of flags.
        result = {
            'jenkins': jenkins,
            'coverage': coverage,
            'ready-to-commit': rtc
        }
        # Check for needed reports.
        self._env.NEED_COVERAGE = jenkins or coverage
        self._env.NEED_TEST_REPORT =  jenkins or rtc
        self._env.NEED_CLOC_XML = jenkins
        self._env.NEED_VALGRIND_REPORT = jenkins or rtc
        self._env.NEED_CPPCKET_XML = jenkins or rtc
        # Add flags to the environment for gtest and gmock.
        aux = [f for f in self._env['CXXFLAGS'] if f not in ['-ansi', '-pedantic']]
        aux.append('-Wno-sign-compare')
        CXXFLAGS = aux
        if not '-ggdb3' in CXXFLAGS:
            CXXFLAGS.append('-ggdb3')
        self._env.Replace(CXXFLAGS=CXXFLAGS, CFLAGS=CXXFLAGS)
        # Check if we need test report.
        if self._env.NEED_TEST_REPORT:
            test_report = self._env.Dir(self._env['INSTALL_REPORTS_DIR'])
            test_report = test_report.Dir('test').Dir(self._project_name)
            self._env.test_report = 'xml:%s/test-report.xml' % test_report.abspath
        # Check if we need the coverage flag.
        if self._env.NEED_COVERAGE:
            flags = ['--coverage']
            self._env.Append(CXXFLAGS=flags, CFLAGS=flags, LINKFLAGS=flags)
            project_component._env.Append(CXXFLAGS=flags, CFLAGS=flags, LINKFLAGS=flags)
        # Check if we need the output of cloc in xml file.
        if self._env.NEED_CLOC_XML:
            project_component._env.Replace(CLOC_OUTPUT_FORMAT='xml')
        # Check if we need the output of cppchec in xml format.
        if self._env.NEED_CPPCKET_XML:
            project_component._env.Append(CPPCHECK_OPTIONS='--xml')
        # Check if we need to create an xml report for valgrind.
        if self._env.NEED_VALGRIND_REPORT:
            # Create the directory to store the valgrind report.
            report_dir = self._env['INSTALL_REPORTS_DIR']
            valgrind_report_dir = self._env.Dir(report_dir).Dir('valgrind')
            valgrind_report_dir = valgrind_report_dir.Dir(self._project_name)
            if not os.path.exists(valgrind_report_dir.abspath):
                os.makedirs(valgrind_report_dir.abspath)
            # Set the path to the report file.
            report_file = '%s/valgrind-report.xml' % valgrind_report_dir.abspath
            flags = ' --xml=yes --xml-file=%s ' % report_file
            self._env.Append(VALGRIND_OPTIONS=flags)
        return result

    def _CreateValgrindTarget(self, program_builder):
        if self._builders['valgrind'] is not None:
            return self._builders['valgrind']
        target = '%s:valgrind' % self._project_name
        # Create an instance of the RunValgrind() builder.
        run_valgrind_builder = self._env.RunValgrind(target, program_builder)
        # Create the alias.
        name = target
        deps = [run_valgrind_builder]
        msg = 'Run valgrind for %s test' % self._project_name
        self._env.Alias(name, deps, msg)
        self._builders['valgrind'] = run_valgrind_builder
        return run_valgrind_builder

    def _CreateCoverageTarget(self, target, program_builder):
        if self._builders['coverage'] is not None:
            return self._builders['coverage']
        # Edit the target
        target = "%s.cov" % target
        # Get the path directory to the project.
        project_component = self._component_graph.get(self._project_name)
        self._env['PROJECT_DIR'] = project_component._dir.abspath
        project_deps = self._dependencies + project_component._dependencies
        project_deps = utils.RemoveDuplicates(project_deps)
        project_deps.remove(self._project_name)
        for dep in project_deps:
            dep_component = self._component_graph.get(dep)
            project_deps += dep_component._dependencies
        project_deps = utils.RemoveDuplicates(project_deps)
        self._env['PROJECT_DEPS'] = project_deps

        # Targets and sources for builder InitLcov().
        init_lcov_target = os.path.join(self._dir.abspath, 'coverage_data')
        init_lcov_soureces = [program_builder]
        # Create an instance of the InitLcov() builder.
        init_lcov_builder = self._env.InitLcov(
            init_lcov_target,
            init_lcov_soureces
        )
        # Create an instance of the RunUnittest() builder.
        run_test_builder = self._env.RunUnittest(target, program_builder)
        # Make the test depends from files in 'ref' dir.
        for refFile in utils.FindFiles(self._env, self._dir.Dir('ref')):
            self._env.Depends(run_test_builder, refFile)
        # Targets and sources for RunLcov() builder.
        reports_dir = self._env['INSTALL_REPORTS_DIR']
        coverage_dir = self._env.Dir(reports_dir).Dir('coverage')
        coverage_dir = coverage_dir.Dir(self._project_name).abspath
        lcov_targets = os.path.join(coverage_dir, 'index.html')
        lcov_sources = [program_builder]
        # Create an instance of the RunLcov() builder.
        run_lcov_builder = self._env.RunLcov(lcov_targets, lcov_sources)
        # Create dependencies between targets.
        self._env.Depends(run_test_builder, init_lcov_builder)
        self._env.Depends(run_lcov_builder, run_test_builder)
        # Create the target for coverage.
        cov = self._env.Alias(
            '%s:coverage' % self._project_name,
            run_lcov_builder,
            'Checks the tests coverage on the project.'
        )
        # Coverage can always be built.
        self._env.AlwaysBuild(cov)
        self._env.AlwaysBuild(run_test_builder)
        self._builders['coverage'] = cov
        return cov

    def _CreateJenkinsTarget(self, flags, target, program_builder):
        if self._builders['jenkins'] is not None:
            return self._builders['jenkins']
        # Get the component of the project.
        project_component = self._component_graph.get(self._project_name)
        # Create the alias.
        jenkins = self._env.Alias(
            '%s:jenkins' % self._project_name,
            None,
            "Build the environmnet's project for the Jenkins server."
        )
        # If the target 'jenkins' was invoked...
        if flags['jenkins']:
            # Get the builders from which the jenkins target will depend on.
            sources = project_component.GetSourcesFiles()
            includes = project_component.GetIncludeFiles()
            source = sources + includes
            astyle_check = project_component._CreateAstyleCheckTarget(source)
            cppcheck = project_component._CreateCppcheckTarget(source)
            cccc = project_component._CreateCCCCTarget(source)
            cloc = project_component._CreateClocTarget(source)
            doc = project_component._CreateDocTarget()
            valgrind = self._CreateValgrindTarget(program_builder)
            coverage = self._CreateCoverageTarget(target, program_builder)
            # Create dependencies.
            self._env.Depends(jenkins, astyle_check)
            self._env.Depends(jenkins, cppcheck)
            self._env.Depends(jenkins, valgrind)
            self._env.Depends(jenkins, coverage)
            self._env.Depends(jenkins, cccc)
            self._env.Depends(jenkins, cloc)
            self._env.Depends(jenkins, doc)
        self._builders['jenkins'] = jenkins
        return jenkins

    def _CreateReadyToCommitTtarget(self, flags, run_test_target, program_builder):
        if self._builders['ready-to-commit'] is not None:
            return self._builders['ready-to-commit']
        # Get the component of the project.
        project_component = self._component_graph.get(self._project_name)
        # Create the alias.
        ready_to_commit = self._env.Alias(
            '%s:ready-to-commit' % self._project_name,
            None,
            "Check if the project is ready to be commited."
        )
        # Create a shorter alias.
        self._env.Alias(
            '%s:rtc' % self._project_name,
            ready_to_commit,
            "Alias of the target: ready-to-commit."
        )
        # If the target 'ready-to-commit' was invoked...
        if flags['ready-to-commit']:
            # Create an instance of the RunReadyToCommit() builder.
            target = self._env.Dir('$INSTALL_REPORTS_DIR')
            target = target.Dir('ready-to-commit').Dir(self._project_name)
            target = target.File('ReadyToCommitReportFile.txt')
            rtc_builder = self._env.RunReadyToCommit(target, None)
            self._env.AlwaysBuild(rtc_builder)
            self._env['PROJECT_NAME'] = self._project_name
            # Get the builders from which the ready-to-commit target will
            # depend on.
            sources = project_component.GetSourcesFiles()
            includes = project_component.GetIncludeFiles()
            source = sources + includes
            astyle_check = project_component._CreateAstyleCheckTarget(source)
            cppcheck = project_component._CreateCppcheckTarget(source)
            valgrind = self._CreateValgrindTarget(program_builder)
            run_test = self._env.RunUnittest(run_test_target, program_builder)
            # Create dependencies.
            self._env.Depends(rtc_builder, astyle_check)
            self._env.Depends(rtc_builder, cppcheck)
            self._env.Depends(rtc_builder, run_test)
            self._env.Depends(rtc_builder, valgrind)
            self._env.Depends(ready_to_commit, rtc_builder)
        self._builders['ready-to-commit'] = ready_to_commit
        return ready_to_commit

    def _UseMocko(self, sources):
        # Path to the list.mocko file.
        mocko_list = self._dir.File('list.mocko')
        # Path to the mocko_bind.cpp file.
        mocko_bind_cpp = self._dir.File('mocko_bind.cpp')
        # Path to the mocko_bind.h file.
        mocko_bind_h = self._dir.File('mocko_bind.h')
        # Path to the mocko_bind.gdb file.
        mocko_bind_gdb = self._dir.File('mocko_bind.gdb')
        # The 'mocko' executable.
        mocko_exe = self._env.Dir('$INSTALL_BIN_DIR').File('mocko')
        # Create an instance of the RunMocko() builder.
        targets = [mocko_bind_h, mocko_bind_cpp, mocko_bind_gdb]
        src = [mocko_list, mocko_exe]
        mocko_builder = self._env.RunMocko(targets, src)
        # Add mocko_bind.cpp to the sources.
        sources.append(mocko_bind_cpp)
        return mocko_builder
