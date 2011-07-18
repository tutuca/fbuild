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
        comp = components[dep]
        if comp.buildDir or comp.forceLib:
            libpaths.append(comp.buildDir)
            libs.append(dep)
        if comp.incDirs:
            incpaths.extend(comp.incDirs)
        (recursiveIncReturn, recursiveLibPathReturn,recursiveLibReturn) = GetDependenciesPaths(env, comp.deps)
        if recursiveIncReturn:
            incpaths.extend(recursiveIncReturn)
        if recursiveLibPathReturn:
            libpaths.extend( recursiveLibPathReturn )
        if recursiveLibReturn:
            libs.extend( recursiveLibReturn )
    return (incpaths, libpaths, libs)

# takes an string or a to_path function parameter, or a list.
def _buildPathList(incDirs, to_path):
    _as_path = lambda _dir: _dir if isinstance(_dir, str) else to_path(_dir)

    if isinstance(incDirs, list) or isinstance(incDirs, tuple):
        return [_as_path(_dir) for _dir in incDirs]
    else:
        return [_as_path(incDirs)]

class Component(object):
    def __init__(self, name, incDirs, deps, buildDir='', forceLib=False):
        self.name = name
        self.incDirs = _buildPathList(incDirs, lambda d: d.abspath)
        self.deps = deps
        self.buildDir = buildDir
        self.forceLib = forceLib
        self.processed = False
        self.sconscriptPath = None

# it has deps because it can pull other libraries
def CreateHeaderOnlyLibrary(env, name, inc, deps):
    if isPreProcessing == True:
        _addComponent(env, name, Component(name, inc, deps))

def CreateProgram(env, name, inc, src, deps):
    if isPreProcessing == True:
        buildDir = os.path.join(env['BUILD_DIR'], name)
        _addComponent(env, name, Component(name, inc, deps, buildDir))
    else:
        (incpaths,libpaths,libs) = GetDependenciesPaths(env, deps)
        hlibEnv = env.Clone()
        program = hlibEnv.Program(name, src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        hlibEnv.Install(env['INSTALL_DIR'], program)

def CreateTest(env, name, inc, src, deps):
    if isPreProcessing == True:
        name = name + ':test'
        buildDir = os.path.join(env['BUILD_DIR'], name)
        _addComponent(env, name, Component(name, inc, deps, buildDir))
    else:
        (incpaths,libpaths,libs) = GetDependenciesPaths(env, deps)
        testEnv = env.Clone()
        global components
        testEnv.PrependENVPath('LD_LIBRARY_PATH', components[name].buildDir)
        test = testEnv.Program(name, src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        testEnv.Test(name + '.passed', test)
        
def CreateStaticLibrary(env, name, inc, src, deps):
    if isPreProcessing == True:
        buildDir = os.path.join(env['BUILD_DIR'], name)
        CreateHeaderOnlyLibrary(env, name + ':include', inc, deps)
        _addComponent(env, name, Component(name, inc, deps, buildDir))
    else:
        (incpaths,libpaths,libs) = GetDependenciesPaths(env, deps)
        incpaths.extend(_buildPathList(inc, lambda d: d.abspath))
        libEnv = env.Clone()
        libEnv.Library(name, src, CPPPATH=incpaths)

# For static libraries we will make a version header only
# of the lib so a component can depend on this one in a light way
def CreateSharedLibrary(env, name, inc, src, deps):
    if isPreProcessing == True:
        buildDir = os.path.join(env['BUILD_DIR'], name)
        _addComponent(env, name, Component(name + ':include', inc, deps, buildDir))
    else:
        (incpaths,libpaths,libs) = GetDependenciesPaths(env, deps)
        incpaths.extend(_buildPathList(inc, lambda d: d.abspath))
        dlibEnv = env.Clone()
        dlib = dlibEnv.SharedLibrary(name, src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        dlibEnv.Install(env['INSTALL_DIR'], dlib)

# Empty build dir means that this is a header only library
def AddComponent(env, name, incDirs, deps, buildDir = '', forceLib = False):
    global components
    components[name] = Component(name, incDirs, deps, buildDir, forceLib)

#Just load all components.
def WalkDirsForComponents(env, topdir, ignore):
    # Step 1: populate all the components
    for root, dirnames, filenames in os.walk(topdir):
        if ignore.count(os.path.relpath(root, env.Dir('#').abspath)) == 0:
            for filename in fnmatch.filter(filenames, 'SConscript'):
                pathname = os.path.join(root, filename)
                _pre_process(env, pathname)

def initializeDependencies(env):
    global downloadableDependencies 
    downloadableDependencies = findLoadableDependencies(env)

def process(env, target):
    global components
    global downloadableDependencies
    component = components.get(target)
    if component:
        for dep in component.deps:
            if not components.has_key(dep):
                downloadableDependency = downloadableDependencies.get(dep)
                if downloadDependency(env, downloadableDependency):
                    pathname = os.path.join(downloadableDependency.target, "SConscript")
                    if not os.path.exists(pathname):
                        raise Exception('Could not found SConscript for: %s' % dep)
                    else:
                        _pre_process(env, pathname)
                else:
                    raise Exception('Could not found dependency: %s' % dep)
            process(env, dep)
        _process_component(env, component)
    else:
        raise Exception('Could not found target: %s' % target)

def _pre_process(env, sconscriptPath):
    global isPreProcessing
    isPreProcessing = True
    env.SConscript(sconscriptPath, exports='env')
    isPreProcessing = False

def _process_component(env, component):
    if component.sconscriptPath and component.buildDir and not component.processed:
        variantPath = component.buildDir
        component.processed = True
        env.SConscript(component.sconscriptPath, variant_dir=variantPath, duplicate=0, exports='env')

#TODO: rename?
def _addComponent(env, name, component):
    global components
    component.sconscriptPath = os.path.join(env.Dir('.').abspath, "SConscript")
    components[name] = component

