# FuDePan boilerplate required here

import fnmatch
import os
import SCons

components = {}
lastAddedComponent = None
isPreProcessing = False

class Component(object):
    def __init__(self, name, buildDir, incDirs, deps, isQt):
        global components
        self.name = name
        self.buildDir = buildDir
        self.incDirs = incDirs
        self.deps = deps
        self.isQt = isQt
    def __hash__(self):
        self.name.__hash__()
    def __eq__(self,other):
        return self.name == other

def AddComponent(env, name, incDirs, deps, isHook = False, isQt = False):
    global components
    global lastAddedComponent
    if components.has_key(name) and components[name] is not None:
        raise Exception('Component already defined: %s' % name)
    # TODO: should I detect circular dependencies? scons already
    # do that at a library level
    buildDir = ''
    if not isHook:
        buildDir = os.path.join(env['BUILD_DIR'], name)
    lastAddedComponent = Component(name, buildDir, incDirs, deps, isQt)
    components[name] = lastAddedComponent
    
# These three functions could be only one to avoid two recursive iterations
# through the dependency tree

def GetIncludePaths(env, deps):
    incpaths = []
    for dep in deps:
        comp = components[dep]
        if comp is None:
            raise Exception('Component %s depends on undefined component %s' % (name, dep) )
        incpaths.append(comp.incDirs)
        recursiveReturn = GetIncludePaths(env, comp.deps)
        if len(recursiveReturn) > 0:
            incpaths.append( recursiveReturn )
    return incpaths

def GetLibPaths(env, deps):
    libpaths = []
    for dep in deps:
        comp = components[dep]
        if comp is None:
            raise Exception('Component %s depends on undefined component %s' % (name, dep) )
        libpaths.append(comp.buildDir)
        recursiveReturn = GetLibPaths(env, comp.deps)
        if len(recursiveReturn) > 0:
            libpaths.append( recursiveReturn )
    return libpaths
    
def GetQtModulesFromDeps(env, deps):
    qtmodules = []
    for dep in deps:
        comp = components[dep]
        if comp is None:
            raise Exception('Component %s depends on undefined component %s' % (name, dep) )
        if comp.isQt:
            qtmodules.append( comp.name )
        recursiveReturn = GetQtModulesFromDeps(env, comp.deps)
        if len(recursiveReturn) > 0:
            qtmodules.append( recursiveReturn )
    return qtmodules
    

def CreateProgram(env, name, inc, src, deps, ui=''):
    if isPreProcessing == True:
        AddComponent(env, name, inc, deps)
    else: 
        incpaths = GetIncludePaths(env, deps)
        incpaths.append(inc.get_abspath())
        libpaths = GetLibPaths(env, deps)
        qtmodules = GetQtModulesFromDeps(env, deps)
        if len(qtmodules) > 0:
            env.EnableQtModules(qtmodules)
        # I live this commented because scons is detecting automatically
        # the required ui
        #if ui != '':
        #    env.Uic(ui)
        program = env.Program(name, src, CPPPATH=incpaths, LIBS=deps, LIBPATH=libpaths)
        install_program = env.Install(env['INSTALL_DIR'], program)

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
        install_dlib = env.Install(env['INSTALL_DIR'], dlib)

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

