# FuDePan boilerplate required here

import fnmatch
import os
import SCons
from dependencies import downloadDependency

components = {}
lastAddedComponent = None
isPreProcessing = False
downloadedDepencencies = False

class Component(object):
    def __init__(self, name, incDirs, deps, buildDir, forceLib):
        global components
        self.name = name
        self.buildDir = buildDir
        self.incDirs = incDirs
        self.deps = deps
        self.forceLib = forceLib
    def __hash__(self):
        self.name.__hash__()
    def __eq__(self,other):
        return self.name == other.name
    def eq(self,other):
        return self.name == other.name and self.buildDir == other.buildDir \
               and self.incDirs == other.incDirs and self.deps == other.deps \
               and self.forceLib == other.forceLib

# Empty build dir means that this is a header only library
def AddComponent(env, name, incDirs, deps, buildDir = '', forceLib = False):
    global components
    global lastAddedComponent
    global downloadedDepencencies
    inputComponent = Component(name, incDirs, deps, buildDir, forceLib)
    if components.has_key(name) and components[name] is not None:
        existentComponent = components[name]
        if existentComponent.eq(inputComponent):
            # We are in the Step 2 of the walk, lets detect thta
            # all dependencies are there
            for dep in deps:
                if not components.has_key(dep) or components[dep] is None:
                    found = downloadDependency(env,dep)
                    if found:
                        downloadedDepencencies = True
                    else:
                        raise Exception('Could not found dependency %s of component %s' % (dep,name))                         
        else:
            raise Exception('Component already defined with different values: %s' % name)
    lastAddedComponent = inputComponent 
    components[name] = lastAddedComponent
    
def GetDependenciesPaths(env, deps):
    incpaths = []
    libpaths = []
    libs = []
    for dep in deps:
        comp = components[dep]
        if comp is None:
            raise Exception('Component %s depends on undefined component %s' % (name, dep) )
        if comp.buildDir != '' or comp.forceLib:
            libpaths.append(comp.buildDir)
            libs.append(comp.name)
        if comp.incDirs != '':
            incpaths.append(comp.incDirs)
        (recursiveIncReturn, recursiveLibPathReturn,recursiveLibReturn) = GetDependenciesPaths(env, comp.deps)
        if len(recursiveIncReturn) > 0:
            incpaths.append(recursiveIncReturn)
        if len(recursiveLibPathReturn) > 0:
            libpaths.append( recursiveLibPathReturn )
        if len(recursiveLibReturn) > 0:
            libs.append( recursiveLibReturn )
    return (incpaths, libpaths, libs)
    
# it has deps because it can pull other libraries
def CreateHeaderOnlyLibrary(env, name, inc, deps):
    if isPreProcessing == True:
        AddComponent(env, name, inc, deps)

def CreateProgram(env, name, inc, src, deps):
    if isPreProcessing == True:
        buildDir = os.path.join(env['BUILD_DIR'], name)
        AddComponent(env, name, inc, deps, buildDir)
    else: 
        (incpaths,libpaths,libs) = GetDependenciesPaths(env, deps)
        incpaths.append(inc.get_abspath())
        program = env.Program(name, src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        install_program = env.Install(env['INSTALL_DIR'], program)

def CreateStaticLibrary(env, name, inc, src, deps):
    if isPreProcessing == True:
        buildDir = os.path.join(env['BUILD_DIR'], name)
        # For static libraries we will make a version header only
        # of the lib so a component can depend on this one in a light way
        CreateHeaderOnlyLibrary(env, name + ':include', inc, deps)
        AddComponent(env, name, inc, deps, buildDir)
    else:
        (incpaths,libpaths,libs) = GetDependenciesPaths(env, deps)
        incpaths.append(inc.get_abspath())
        lib = env.Library(name, src, CPPPATH=incpaths)

def CreateSharedLibrary(env, name, inc, src, deps):
    if isPreProcessing == True:
        buildDir = os.path.join(env['BUILD_DIR'], name)
        # For shared libraries we will make a version header only
        # of the lib so a component can depend on this one in a light way
        CreateHeaderOnlyLibrary(env, name + ':include', inc, deps)
        AddComponent(env, name, inc, deps, buildDir)
    else:
        (incpaths,libpaths,libs) = GetDependenciesPaths(env, deps)
        incpaths.append(inc.get_abspath())
        dlib = env.SharedLibrary(name, src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        install_dlib = env.Install(env['INSTALL_DIR'], dlib)

def WalkDirsForComponents(env, topdir):
    global isPreProcessing
    global downloadedDepencencies
    sconsPaths = []
    # We are doing two passes, pass one is to fill
    # the component definition, pass two is the actual
    # SConscript walk. In order to get the component info,
    # the global variable isPreProcessing is used
    # To do the second step faster, we use the sconsPaths
    # variable
    isPreProcessing = True
    # Step 1: populate all the components
    for root, dirnames, filenames in os.walk(topdir):
        for filename in fnmatch.filter(filenames, 'SConscript'):
            pathname = os.path.join(root, filename)
            env.SConscript(pathname, exports='env')
            
    # Step 2: verify downloadable dependencies            
    downloadedDepencencies = True
    while downloadedDepencencies:
        downloadedDepencencies = False
        del sconsPaths[:]
        for root, dirnames, filenames in os.walk(topdir):
            for filename in fnmatch.filter(filenames, 'SConscript'):
                pathname = os.path.join(root, filename)
                env.SConscript(pathname, exports='env')
                sconsPaths.append( (root,lastAddedComponent.name) )
    # Step 3: real SConscript walk
    isPreProcessing = False
    for (sconsPath,componentName) in sconsPaths:
        variantPath = os.path.join(env['BUILD_DIR'], componentName)
        sconscriptPath = os.path.join(sconsPath,'SConscript')
        env.SConscript(sconscriptPath, variant_dir=variantPath, duplicate=0, exports='env')

