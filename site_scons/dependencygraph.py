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

#
# Description: this file contains a graph with dependencies between the
#              components to better solve include paths and library linking
#


import fnmatch
import os

from SCons.Script.SConscript import SConsEnvironment

from core_components import *
from components import *
import fbuild_exceptions


downloadedDependencies = False


def init(env):
    SConsEnvironment.CreateObject = CreateObject
    SConsEnvironment.CreateProgram = CreateProgram
    SConsEnvironment.CreateExternalComponent = CreateExternalComponent
    SConsEnvironment.CreateStaticLibrary = CreateStaticLibrary
    SConsEnvironment.CreateSharedLibrary = CreateSharedLibrary
    SConsEnvironment.CreateHeaderOnlyLibrary = CreateHeaderOnlyLibrary
    SConsEnvironment.CreateTest = CreateTest
    SConsEnvironment.CreatePdfLaTeX = CreatePdfLaTeX
    #SConsEnvironment.CreateAutoToolsProject = CreateAutoToolsProject


class ComponentDictionary(dict):

    def Add(self, component, check=True):
        if check:
            if not component.name.islower():
                component.env.Cprint('[warn] modules names should be lower case: ' + component.name, 'yellow')
        # Its possible that a component is tried to be added twice because a new
        # dependency was downloaded and
        if component.name not in self:
            self[component.name] = component
            return component
        else:
            component.env.Cprint('[warn] component tried to be re-added %s' % component.name, 'red')

    def GetComponentsNames(self):
        return self.keys()

componentGraph = ComponentDictionary()


def CreateExternalComponent(env, name, ext_inc, libPath, deps, shouldBeLinked, aliasGroups=None):
    aliasGroups = aliasGroups if aliasGroups is not None else []
    return componentGraph.Add(ExternalComponent(componentGraph,
                                                env,
                                                name,
                                                libPath,
                                                deps,
                                                ext_inc,
                                                shouldBeLinked,
                                                aliasGroups),
                               False)


def CreateHeaderOnlyLibrary(env, name, inc, deps, aliasGroups=None):
    aliasGroups = aliasGroups if aliasGroups is not None else []
    return componentGraph.Add(HeaderOnlyComponent(componentGraph,
                                           env,
                                           name,
                                           env.Dir('.'),
                                           deps,
                                           inc,
                                           aliasGroups))


def CreateStaticLibrary(env, name, inc, ext_inc, src, deps, aliasGroups=None):
    aliasGroups = aliasGroups if aliasGroups is not None else []
    return componentGraph.Add(StaticLibraryComponent(componentGraph,
                                              env,
                                              name,
                                              env.Dir('.'),
                                              deps,
                                              inc,
                                              ext_inc,
                                              src,
                                              aliasGroups))


def CreateSharedLibrary(env, name, inc, ext_inc, src, deps, aliasGroups=None):
    aliasGroups = aliasGroups if aliasGroups is not None else []
    return componentGraph.Add(DynamicLibraryComponent(componentGraph,
                                               env,
                                               name,
                                               env.Dir('.'),
                                               deps,
                                               inc,
                                               ext_inc,
                                               src,
                                               aliasGroups))


def CreateObject(env, name, inc, src, deps, aliasGroups=None):
    aliasGroups = aliasGroups if aliasGroups is not None else []
    return componentGraph.Add(ObjectComponent(componentGraph,
                                       env,
                                       name,
                                       env.Dir('.'),
                                       deps,
                                       inc,
                                       src,
                                       aliasGroups))


def CreateProgram(env, name, inc, src, deps, aliasGroups=None):
    aliasGroups = aliasGroups if aliasGroups is not None else []
    return componentGraph.Add(ProgramComponent(componentGraph,
                                        env,
                                        name,
                                        env.Dir('.'),
                                        deps,
                                        inc,
                                        src,
                                        aliasGroups))


def CreateTest(env, name, inc, src, deps, aliasGroups=None):
    aliasGroups = aliasGroups if aliasGroups is not None else []
    # Change the name so we can add the component to the graph.
    testName = '%s@test' % name
    # The test automatically depends on the thing that is testing
    if name not in deps:
        deps.append(name)
    else:
        msg = '[WARNING] %s: In test SConscript - Project added as a dependency of its test.' % name
        env.Cprint(msg, 'yellow')
    return componentGraph.Add(UnitTestComponent(componentGraph,
                                         env,
                                         testName,
                                         env.Dir('.'),
                                         deps,
                                         inc,
                                         src,
                                         aliasGroups))


def CreatePdfLaTeX(env, name, latexfile='', options='', aliasGroups=None):
    aliasGroups = aliasGroups if aliasGroups is not None else []
    docName = name + ':pdf:' + latexfile
    latexfile = env['INSTALL_DOC_DIR'] + "/" + name + ":doc/latex/" + latexfile
    env['PDFLATEX_OPTIONS'] = options
    return componentGraph.Add(PdfLaTeXComponent(componentGraph,
                                    env,
                                    docName,
                                    env.Dir('.'),
                                    latexfile,
                                    aliasGroups))


#def CreateAutoToolsProject(env, name, ext_dir, lib_targets, configurationFile, aliasGroups=None):
    #if aliasGroups == None:
        #aliasGroups = []
    #return componentGraph.Add(AutoToolsProjectComponent(componentGraph,
                                        #env,
                                        #name,
                                        #env.Dir('.'),
                                        #ext_dir,
                                        #lib_targets,
                                        #configurationFile,
                                        #aliasGroups))


def WalkDirsForSconscripts(env, topdir, ignore=None):
    global componentGraph
    global downloadedDependencies

    ignore = ignore if ignore is not None else []

    # Step 1: load all the components in the dependency graph
    # if we find a download dependency, we download it and re-process
    # everything to be sure that all the components are downloaded and
    # loaded in the dependency graph Initial set to pass the loop test
    originalGraph = componentGraph.copy()

    for component in env.ExternalDependenciesCreateComponentsDict.keys():
        exec env.ExternalDependenciesCreateComponentsDict[component] in {'env': env}

    downloadedDependencies = True
    while downloadedDependencies:
        downloadedDependencies = False
        for root, dirnames, filenames in os.walk(topdir):
            if ignore.count(os.path.relpath(root, topdir)) == 0:
                for filename in fnmatch.filter(filenames, 'SConscript'):
                    pathname = os.path.join(root, filename)
                    vdir = os.path.join(
                        env['BUILD_DIR'],
                        os.path.relpath(root, env['WS_DIR'])
                    )
                    # We clone the enviroment since we need different one for each
                    # project.
                    env2 = env
                    env = env.Clone()
                    env.SConscript(
                        pathname,
                        exports='env',
                        variant_dir=vdir,
                        duplicate=1
                    )
                    env = env2
        # Check if there is a component that we dont know how to build
        for component in componentGraph.GetComponentsNames():
            downloadedDependencies = _InstallComponentAndDep(env, component)
            if downloadedDependencies:
                break
            # If a dependency was downloaded we need to re-parse all the
            # SConscripts to assurance not to try to download something that
            # is added by another component (i.e.: gtest_main is added by gmock)
        if downloadedDependencies:
            # Reset this to allow it to reparse those that were already added
            componentGraph.clear()
            componentGraph.update(originalGraph)
            for component in env.ExternalDependenciesCreateComponentsDict.keys():
                d = {'env': env}
                exec env.ExternalDependenciesCreateComponentsDict[component] in d

    # Step 2: real processing we have everything loaded in the dependency graph
    # now we process it

    for componentName in componentGraph.GetComponentsNames():
        component = componentGraph.get(componentName)
        component.Process()

def _InstallComponentAndDep(env, component_name):
    comp_queue = [component_name]
    downloadedDependencies = False
    while comp_queue:
        # Take the first element in the queue
        comp = comp_queue.pop(0)
        component = componentGraph.get(comp)
        if component is not None:
            dep_list_comp = component._dependencies
        else:
            dep_list_comp = env.GetComponentDeps(comp)
        # We remove from the list dependencies already installed.
        dep_list_comp = [dep for dep in dep_list_comp if componentGraph.get(dep) is None]

        if dep_list_comp:
            for dep in dep_list_comp:
                if not dep in comp_queue:
                    comp_queue.append(dep)
        if component is None:
            downloadedDependencies = env.CheckoutDependencyNow(comp, env)
    return downloadedDependencies
