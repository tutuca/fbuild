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

# FuDePAN boilerplate required here

import fnmatch
import os
import SCons
import dependencies
import recursive_install
import shutil

isPreProcessing = False
SConscriptFiles = {}
components = {}
downloadableDependencies = []

def GetDependenciesPaths(compName, env, deps):
    def search(deps):
        libpaths = []
        libs = []
        incs = []
        for dep in deps:
            comp = _findComponent(dep)
            if comp.external:
                incs += comp.headerDirs
            if comp.type == 'static_lib':
                libpaths.append(comp.buildDir)
            if comp.type in ["static_lib", "shared_lib", 'lib', 'autotools']:
                libs.append(dep)
            (recursiveLibPathReturn, recursiveLibReturn, recursiveIncs) = search(comp.deps)
            libpaths.extend(recursiveLibPathReturn)
            libs.extend(recursiveLibReturn)
            incs.extend(recursiveIncs)
        return (libpaths, libs, incs)
    comp = _findComponent(compName)
    libpaths, libs, incs = search(deps)
    if comp:
        incpaths = incs + [env['INSTALL_HEADERS_DIR']] + _buildPathList(comp.headerDirs, lambda d: d.abspath)
    else:
        incpaths = incs + [env['INSTALL_HEADERS_DIR']]
    libpaths.append(env['INSTALL_LIB_DIR'])
    return (incpaths, libpaths, libs)

# takes an string or a to_path function parameter, or a list.
def _buildPathList(headerDirs, to_path):
    _as_path = lambda _dir: _dir if isinstance(_dir, str) else to_path(_dir)

    if isinstance(headerDirs, list) or isinstance(headerDirs, tuple):
        return [_as_path(_dir) for _dir in headerDirs]
    else:
        return [_as_path(headerDirs)]

class Component(object):
    def __init__(self, name, headerDirs, deps, buildDir, installIncludesDir, externalHeaderDirs, type):
        self.name = name
        self.headerDirs = _buildPathList(headerDirs, lambda d: d.abspath)
        self.externalHeaderDirs = _buildPathList(externalHeaderDirs, lambda d: d.abspath) if externalHeaderDirs else None
        self.buildDir = buildDir
        self.installIncludesDir = installIncludesDir
        self.deps = deps
        self.sconscriptPath = None
        self.processed = False
        self.type = type
        self.external = False
        self.refDir = ''

    def copyHeaders(self, env):
        if not self.processed and self.externalHeaderDirs:
            for d in self.externalHeaderDirs:
                for f in os.listdir(d):
                    if not f.startswith('.'):
                        path = os.path.join(d, f)
                        if os.path.isdir(path):
                            recursive_install.RecursiveInstall(env, self.installIncludesDir, path)
                        else:
                            t = env.Install(self.installIncludesDir, path)
                            env.jAlias('all:install', t, "install all targets")
            self.processed = True #TODO: gtest_main.abspath()

def setupComponent(env, type, name, inc, deps=[], externalHeaderDirs=None):
    buildDir = os.path.join(env['BUILD_DIR'], name)
    installIncludesDir = os.path.join(env['INSTALL_HEADERS_DIR'], name)
    return Component(name, inc, deps, buildDir, installIncludesDir, externalHeaderDirs, type)

# it has deps because it can pull other libraries
def CreateHeaderOnlyLibrary(env, name, inc, ext_inc, deps):
    if isPreProcessing:
        _addComponent(env, name, setupComponent(env, 'header_only', name, inc, deps, ext_inc))
    else:
        _findComponent(name).copyHeaders(env)

def CreateProgram(env, name, inc, src, deps):
    if isPreProcessing:
        _addComponent(env, name, setupComponent(env, 'program', name, inc, deps))
    else:
        (incpaths,libpaths,libs) = GetDependenciesPaths(name, env, deps)
        progEnv = env.Clone()
        program = progEnv.Program(name, src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        progEnv.jAlias('all:build', program, "build all targets")
        install = progEnv.Install(env['INSTALL_BIN_DIR'], program)
        progEnv.jAlias(name, install, "build and install " + name)
        progEnv.jAlias('all:install', install, "install all targets")

def CreateTest(env, name, inc, src, deps):
    if isPreProcessing:
        name = name + ':test'
        _addComponent(env, name, setupComponent(env, 'test', name, inc, deps))
        refPath = os.path.join(env.Dir('.').abspath, 'ref')
        if os.path.isdir(refPath):
            testComponent = _findComponent(name);
            testComponent.refDir = refPath
    else:
        (incpaths,libpaths,libs) = GetDependenciesPaths(name, env, deps)
        libEnv = env.Clone()
        testEnv = env.Clone()
        component = _findComponent(name)
        if not component:
            raise Exception('The unit test is trying to test component %s which does not exists' % name)
        else:            
            buildDir = component.buildDir
            testEnv.PrependENVPath('LD_LIBRARY_PATH', buildDir)
            testEnv.Append(RPATH = ':' + buildDir)
            for p in libpaths: 
                testEnv.PrependENVPath('LD_LIBRARY_PATH', p)
                testEnv.Append(RPATH = ':' + p)
            tname = name + ':test'
            testComponent = _findComponent(tname)
            # TODO: remove this hack, but put a better way to handle reference files
            if os.path.isdir(testComponent.refDir):
                dstRefPath = os.path.join(os.path.split(src[0].abspath)[0], 'ref')
                if os.path.isdir(dstRefPath):
                    shutil.rmtree(dstRefPath)
                shutil.copytree(testComponent.refDir, dstRefPath)
            test = testEnv.Program(tname, src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
            testEnv.jAlias('all:build', test, "build all targets")
            runtest = testEnv.Test(tname + '.passed', test)
            testEnv.jAlias(tname, runtest, "run " + name + " tests")
            testEnv.jAlias('all:test', runtest, "run all targets")
        
def CreateStaticLibrary(env, name, inc, ext_inc, src, deps):
    if isPreProcessing:
        _addComponent(env, name, setupComponent(env, 'static_lib', name, inc, deps, ext_inc))
    else:
        (incpaths,libpaths,libs) = GetDependenciesPaths(name, env, deps)
        libEnv = env.Clone()
        _findComponent(name).copyHeaders(libEnv)
        compLib = libEnv.Library(name, src, CPPPATH=incpaths)
        libEnv.jAlias(name, compLib, "build " + name)
        libEnv.jAlias('all:build', compLib, "build all targets")

def CreateDoc(env, name, doxyfile=None):
    if isPreProcessing:
        docEnv = env.Clone()
        if doxyfile == None:
            doxyfile = env.Glob('SConscript')
        createDoc = docEnv.Doxygen(name + ':doc', doxyfile)
        docEnv.jAlias(name + ':doc', createDoc, "generates documentation for " + name)

# For static libraries we will make a version header only
# of the lib so a component can depend on this one in a light way
def CreateSharedLibrary(env, name, inc, ext_inc, src, deps):
    if isPreProcessing:
        _addComponent(env, name, setupComponent(env, 'shared_lib', name, inc, deps, ext_inc))
    else:
        (incpaths,libpaths,libs) = GetDependenciesPaths(name, env, deps)
        dlibEnv = env.Clone()
        _findComponent(name).copyHeaders(dlibEnv)
        dlib = dlibEnv.SharedLibrary(name, src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        install = dlibEnv.Install(env['INSTALL_LIB_DIR'], dlib)
        dlibEnv.jAlias(name, install, "install " + name)
        dlibEnv.jAlias('all:build', dlib, "build all targets")
        dlibEnv.jAlias('all:install', install, "install all targets")

def CreateAutoToolsProject(env, name, libfile, configureFile, ext_inc):
    if isPreProcessing:
        _addComponent(env, name, setupComponent(env, 'autotools', name, [], [], []))
    else:
        component = _findComponent(name)
        buildDir = component.buildDir
        libEnv = env.Clone()
        target = [ os.path.join(env['INSTALL_LIB_DIR'], libfile) ]
        target += [os.path.join(component.installIncludesDir, f.name) for f in ext_inc]
        if not os.path.exists(buildDir):
            os.makedirs(buildDir)
        c = libEnv.Configure(target, 'configure', buildDir=buildDir, configurePath=configureFile.abspath)
        libEnv.jAlias(name, c, "build " + name)
        libEnv.jAlias('all:build', c, "build all targets")
        libEnv.jAlias('all:install', c, "install all targets")

def AddComponent(env, name, headerDirs, deps, buildDir = '', isLib = False):
    global components
    component = Component(name, headerDirs, deps, buildDir, '', None, 'lib' if isLib else 'component')
    component.processed = True
    component.external = True
    components[name] = component

#Just load all components.
def WalkDirsForComponents(env, topdir, ignore = []):
    # Step 1: populate all the components
    for root, dirnames, filenames in os.walk(topdir):
        if ignore.count(os.path.relpath(root, topdir)) == 0:
            for filename in fnmatch.filter(filenames, 'SConscript'):
                pathname = os.path.join(root, filename)
                _pre_process_component(env, pathname)

def DownloadDependencyAction(target, source, env):
    global components
    for t in target:
        project = str(t).split(':')[0]
        downloadableDependency = env['DOWNLOADABLE_PROJECTS'].get(project)
        downloadableDependency.download()
        WalkDirsForComponents(env, env['WS_DIR'] + '/' + project)
        for target in list(components):
            process(env, target)
        
def UpdateDependencyAction(target, source, env):
    for t in target:
        project = str(t).split(':')[0]
        downloadableDependency = env['DOWNLOADABLE_PROJECTS'].get(project)
        downloadableDependency.update()

def initializeDependencies(env):
    confDir = env.Dir('#/conf/').abspath
    downloadableDependencies = dependencies.findLoadableDependencies(env, confDir)
    for key in downloadableDependencies.keys():
        if env.Dir(env['WS_DIR'] + '/' + key).exists():
            env.AlwaysBuild(env.Alias(key + ':update', [], UpdateDependencyAction))
            env.jAddAliasDescription(key + ':update', 'update ' + key)
            env.jAlias('all:update', key+':update', 'updates all the checked-out projects')
        else:
            env.AlwaysBuild(env.Alias(key + ':checkout', [], DownloadDependencyAction))
            env.jAddAliasDescription(key + ':checkout', 'checkout ' + key)
    env['DOWNLOADABLE_PROJECTS'] = downloadableDependencies

def process(env, target):
    global components
    downloadableDependencies = env['DOWNLOADABLE_PROJECTS']
	
    component = _findComponent(target)
    if component:
        for dep in component.deps:
            if not components.has_key(dep):
                downloadableDependency = downloadableDependencies.get(dep)
                denv = env.Clone()
                denv['EXTERNAL_DIR'] = env.Dir('#/site_scons/external').abspath
                denv['ROOT'] = env.Dir('#').abspath
                if dependencies.downloadDependency(downloadableDependency, denv):
                    WalkDirsForComponents(env, downloadableDependency.target)
                    for target in list(components):
                        process(env, target)
                else:
                    raise Exception('Could not found dependency: %s' % dep)
            process(env, dep)
        _process_component(env, component)
    else:
        raise Exception('Could not found target: %s' % target)

def _pre_process_component(_env, sconscriptPath):
    global isPreProcessing
    isPreProcessing = True
    env = _env.Clone()
    env.SConscript(sconscriptPath, exports='env')
    isPreProcessing = False

def _process_component(_env, component):
    if component.sconscriptPath and not component.processed:
        env = _env.Clone()
        if component.type == 'test':
            env.SConscript(component.sconscriptPath, variant_dir=component.buildDir, duplicate=0, exports='env', src_dir='..')
        else:
            env.SConscript(component.sconscriptPath, variant_dir=component.buildDir, duplicate=0, exports='env')
        component.processed = True

#TODO: rename?
def _addComponent(env, name, component):
    global components
    if not name.lower() == name:
        env.cprint('[warn] modules names should be lower case: ' + name, 'yellow')
    component.sconscriptPath = os.path.join(env.Dir('.').abspath, "SConscript")
    component.projectDir = env.Dir('.').abspath
    components[name] = component

def _findComponent(name):
    return components.get(name)
