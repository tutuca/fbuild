# FuDePan boilerplate required here

import fnmatch
import os
import SCons

components = {}
lastAddedComponent = None
isPreProcessing = False

class Component(object):
    def __init__(self, name, buildDir, incDirs, deps):
        global components
        self.name = name
        self.buildDir = buildDir
        self.incDirs = incDirs
        self.deps = deps
    def __hash__(self):
        self.name.__hash__()
    def __eq__(self,other):
        return self.name == other

def AddComponent(env, name, incDirs, deps):
    global components
    global lastAddedComponent
    if components.has_key(name) and components[name] is not None:
        raise Exception('Component already defined: %s' % name)
    # TODO: should I detect circular dependencies? scons already
    # do that at a library level
    lastAddedComponent = Component(name, os.path.join(env['BUILD_DIR'], name), incDirs, deps)
    components[name] = lastAddedComponent
    

def GetIncludePaths(env, deps):
    incpaths = []
    for dep in deps:
        comp = components[dep]
        if comp is None:
            raise Exception('Component %s depends on undefined component %s' % (name, dep) )
        incpaths.append(comp.incDirs.get_abspath())
        for recDep in comp.deps:
            recComp = components[recDep]
            if recComp is None:
                raise Exception('Component %s depends on undefined component %s' % (comp.name, recDep) )
            incpaths.append(recComp.incDirs.get_abspath())
    return incpaths

def GetLibPaths(env, deps):
    libpaths = []
    for dep in deps:
        comp = components[dep]
        if comp is None:
            raise Exception('Component %s depends on undefined component %s' % (name, dep) )
        libpaths.append(comp.buildDir)
        for recDep in comp.deps:
            recComp = components[recDep]
            if recComp is None:
                raise Exception('Component %s depends on undefined component %s' % (comp.name, recDep) )
            libpaths.append(recComp.buildDir)
    return libpaths

def CreateProgram(env, name, inc, src, deps):
    if isPreProcessing == True:
        AddComponent(env, name, inc, deps)
    else: 
        incpaths = GetIncludePaths(env, deps)
        incpaths.append(inc.get_abspath())
        libpaths = GetLibPaths(env, deps)
        program = env.Program(name, src, CPPPATH=incpaths, LIBS=deps, LIBPATH=libpaths)
        env.Install(env['INSTALL_DIR'], program)
   
def CreateStaticLibrary(env, name, inc, src, deps):
    if isPreProcessing == True:
        AddComponent(env, name, inc, deps)
    else: 
        incpaths = GetIncludePaths(env, deps)
        incpaths.append(inc.get_abspath())
        libpaths = GetLibPaths(env, deps)  
        lib = env.Library(name, src, CPPPATH=incpaths)

def CreateSharedLibrary(env, name, inc, src, deps):
    if isPreProcessing == True:
        AddComponent(env, name, inc, deps)
    else:
        incpaths = GetIncludePaths(env, deps)
        incpaths.append(inc.get_abspath())
        libpaths = GetLibPaths(env, deps)  
        dlib = env.SharedLibrary(name, src, CPPPATH=incpaths, LIBS=deps, LIBPATH=libpaths)
        env.Install(env['INSTALL_DIR'], dlib)

def WalkDirsForComponents(env, topdir):
    global isPreProcessing
    sconsPaths = []
    # We are doing two passes, pass one is to fill
    # the component definition, pass two is the actual
    # SConscript walk. In order to get the component info,
    # the global variable isPreProcessing is used
    # To do the second step faster, we use the sconsPaths
    # variable
    isPreProcessing = True
    for root, dirnames, filenames in os.walk(topdir):
        for filename in fnmatch.filter(filenames, 'SConscript'):
            pathname = os.path.join(root, filename)
            env.SConscript(pathname, exports='env')
            sconsPaths.append( (root,lastAddedComponent.name) )
    
    isPreProcessing = False
    for (sconsPath,componentName) in sconsPaths:
        variantPath = os.path.join(env['BUILD_DIR'], componentName)
        sconscriptPath = os.path.join(sconsPath,'SConscript')
        env.SConscript(sconscriptPath, variant_dir=variantPath, duplicate=0, exports='env')

