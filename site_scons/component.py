# FuDePan boilerplate required here

import fnmatch
import os
import SCons
from dependencies import downloadDependency
from dependencies import findLoadableDependencies

isPreProcessing = False
SConscriptFiles = {}
components = {}
downloadableDependencies = []

def GetDependenciesPaths(env, deps):
    incpaths = []
    libpaths = []
    libs = []
    for dep in deps:
        comp = _findComponent(dep)
        if comp.isLib:
            libpaths.append(comp.buildDir)
            libs.append(dep)
        if comp.headerDirs:
            incpaths.extend(comp.headerDirs)
        (recursiveIncReturn, recursiveLibPathReturn,recursiveLibReturn) = GetDependenciesPaths(env, comp.deps)
        incpaths.extend(recursiveIncReturn)
        libpaths.extend(recursiveLibPathReturn)
        libs.extend(recursiveLibReturn)
    return (incpaths, libpaths, libs)

# takes an string or a to_path function parameter, or a list.
def _buildPathList(headerDirs, to_path):
    _as_path = lambda _dir: _dir if isinstance(_dir, str) else to_path(_dir)

    if isinstance(headerDirs, list) or isinstance(headerDirs, tuple):
        return [_as_path(_dir) for _dir in headerDirs]
    else:
        return [_as_path(headerDirs)]

class Component(object):
    def __init__(self, name, headerDirs, deps, buildDir, installIncludesDir, externalHeaderDirs, isLib=False):
        self.name = name
        self.headerDirs = _buildPathList(headerDirs, lambda d: d.abspath)
        self.externalHeaderDirs = _buildPathList(externalHeaderDirs, lambda d: d.abspath) if externalHeaderDirs else None
        self.buildDir = buildDir
        self.installIncludesDir = installIncludesDir
        self.deps = deps
        self.isLib = isLib
        self.sconscriptPath = None
        self.processed = False

    def copyHeaders(self, env):
        if not self.processed and self.externalHeaderDirs:
            for d in self.externalHeaderDirs:
                for f in os.listdir(d):
                    if not f.startswith('.'):
                        path = os.path.join(d, f)
                        t = env.Install(self.installIncludesDir, path)
                        env.Alias('install', self.installIncludesDir)
            self.processed = True #TODO: gtest_main

def setupComponent(env, name, inc, deps, isLib, externalHeaderDirs=None):
    buildDir = os.path.join(env['BUILD_DIR'], name)
    installIncludesDir = os.path.join(env['INSTALL_HEADERS_DIR'], name)
    return Component(name, inc, deps, buildDir, installIncludesDir, externalHeaderDirs, isLib)

# it has deps because it can pull other libraries
def CreateHeaderOnlyLibrary(env, name, inc, ext_inc, deps):
    if isPreProcessing:
        _addComponent(env, name, setupComponent(env, name, inc, deps, False, ext_inc))
    else:
        _findComponent(name).copyHeaders(env)

def CreateProgram(env, name, inc, src, deps):
    if isPreProcessing:
        _addComponent(env, name, setupComponent(env, name, inc, deps, False))
    else:
        (incpaths,libpaths,libs) = GetDependenciesPaths(env, deps)
        progEnv = env.Clone()
        program = progEnv.Program(name, src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        install = progEnv.Install(env['INSTALL_BIN_DIR'], program)
        progEnv.Alias(name, install)

def CreateTest(env, name, inc, src, deps):
    if isPreProcessing:
        name = name + ':test'
        _addComponent(env, name, setupComponent(env, name, inc, deps, False))
    else:
        (incpaths,libpaths,libs) = GetDependenciesPaths(env, deps)
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
            name = name + ':test'
            test = testEnv.Program(name, src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
            runtest = testEnv.Test(name + '.passed', test)
            testEnv.Alias(name, runtest)
        
def CreateStaticLibrary(env, name, inc, ext_inc, src, deps):
    if isPreProcessing:
        _addComponent(env, name, setupComponent(env, name, inc, deps, True, ext_inc))
    else:
        (incpaths,libpaths,libs) = GetDependenciesPaths(env, deps)
        incpaths.extend(_buildPathList(inc, lambda d: d.abspath))
        libEnv = env.Clone()
        _findComponent(name).copyHeaders(libEnv)
        compLib = libEnv.Library(name, src, CPPPATH=incpaths)
        libEnv.Alias(name, compLib)        

# For static libraries we will make a version header only
# of the lib so a component can depend on this one in a light way
def CreateSharedLibrary(env, name, inc, ext_inc, src, deps):
    if isPreProcessing:
        _addComponent(env, name, setupComponent(env, name, inc, deps, True, ext_inc))
    else:
        (incpaths,libpaths,libs) = GetDependenciesPaths(env, deps)
        incpaths.extend(_buildPathList(inc, lambda d: d.abspath))
        dlibEnv = env.Clone()
        _findComponent(name).copyHeaders(dlibEnv)
        dlib = dlibEnv.SharedLibrary(name, src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        install = dlibEnv.Install(env['INSTALL_LIB_DIR'], dlib)
        dlibEnv.Alias(name, install)

def AddComponent(env, name, headerDirs, deps, buildDir = '', isLib = False):
    global components
    component = Component(name, headerDirs, deps, buildDir, '', None, isLib)
    component.processed = True
    components[name] = component

#Just load all components.
def WalkDirsForComponents(env, topdir, ignore):
    # Step 1: populate all the components
    for root, dirnames, filenames in os.walk(topdir):
        if ignore.count(os.path.relpath(root, env.Dir('#').abspath)) == 0:
            for filename in fnmatch.filter(filenames, 'SConscript'):
                pathname = os.path.join(root, filename)
                _pre_process_component(env, pathname)

def initializeDependencies(env):
    global downloadableDependencies 
    downloadableDependencies = findLoadableDependencies(env)

def process(env, target):
    global components
    global downloadableDependencies
	
    component = _findComponent(target)
    if component:
        for dep in component.deps:
            if not components.has_key(dep):
                d = _findComponent(dep)
                if d and not d.processed:
                    env.Depends(component.name, dep)
                downloadableDependency = downloadableDependencies.get(dep)
                if downloadDependency(env, downloadableDependency):
                    pathname = os.path.join(downloadableDependency.target, "SConscript")
                    if not os.path.exists(pathname):
                        raise Exception('Could not found SConscript for: %s' % dep)
                    else:
                        _pre_process_component(env, pathname)
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
        src_dir = '..' if component.name.endswith(':test') else None
        env = _env.Clone()
        env.SConscript(component.sconscriptPath, variant_dir=component.buildDir, duplicate=0, exports='env', src_dir=src_dir)
        component.processed = True

#TODO: rename?
def _addComponent(env, name, component):
    global components
    component.sconscriptPath = os.path.join(env.Dir('.').abspath, "SConscript")
    components[name] = component

def _findComponent(name):
    return components.get(name)
