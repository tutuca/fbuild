# FuDePan boilerplate required here

import fnmatch
import os
import SCons
from dependencies import downloadDependency

components = {}
lastAddedComponent = None
isPreProcessing = False
isDetectingDependencies = False
downloadedDependencies = False

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
    global downloadedDependencies
    incs = []
    if type(incDirs).__name__ == 'Dir':
        incs.append( incDirs.abspath )
    else:
        for incDir in incDirs:  
            incs.append( incDir.abspath )
    inputComponent = Component(name, incs, deps, buildDir, forceLib)
    if isDetectingDependencies:
        # We are in the Step 2 of the walk, lets detect that
        # all dependencies are there
        for dep in deps:
            #print 'Parsing dependency %s' % dep
            if not components.has_key(dep) or components[dep] is None:
                found = downloadDependency(env,dep)
                if found:
                   downloadedDependencies = True
                   break
                elif not downloadedDependencies:
                   raise Exception('Could not found dependency %s of component %s' % (dep,name))          
    if not downloadedDependencies:
        #print 'Added component: %s' % name               
        lastAddedComponent = inputComponent 
        components[name] = lastAddedComponent
    #else:
        #print 'Some dependency was downloaded for component: %s' % name
    
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
        hlibEnv = env.Clone()
        program = hlibEnv.Program(name, src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        install_program = hlibEnv.Install(env['INSTALL_DIR'], program)

def CreateTest(env, name, inc, src, deps):
    name = name + ':test'
    if isPreProcessing == True:
        buildDir = os.path.join(env['BUILD_DIR'], name)
        AddComponent(env, name, inc, deps, buildDir)
    else: 
        (incpaths,libpaths,libs) = GetDependenciesPaths(env, deps)
        incpaths.append(inc.get_abspath())
        testEnv = env.Clone()
        test = testEnv.Program(name, src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        # Run test
        env.Test( name + '.passed', test)
        
def CreateStaticLibrary(env, name, inc, src, deps):
    if isPreProcessing == True:
        buildDir = os.path.join(env['BUILD_DIR'], name)
        # For static libraries we will make a version header only
        # of the lib so a component can depend on this one in a light way
        CreateHeaderOnlyLibrary(env, name + ':include', inc, deps)
        AddComponent(env, name, inc, deps, buildDir)
    else:
        (incpaths,libpaths,libs) = GetDependenciesPaths(env, deps)
        incpaths.append(inc)
        libEnv = env.Clone()
        lib = libEnv.Library(name, src, CPPPATH=incpaths)

def CreateSharedLibrary(env, name, inc, src, deps):
    if isPreProcessing == True:
        buildDir = os.path.join(env['BUILD_DIR'], name)
        # For shared libraries we will make a version header only
        # of the lib so a component can depend on this one in a light way
        CreateHeaderOnlyLibrary(env, name + ':include', inc, deps)
        AddComponent(env, name, inc, deps, buildDir)
    else:
        (incpaths,libpaths,libs) = GetDependenciesPaths(env, deps)
        incpaths.append(inc)
        dlibEnv = env.Clone()
        dlib = dlibEnv.SharedLibrary(name, src, CPPPATH=incpaths, LIBS=libs, LIBPATH=libpaths)
        install_dlib = dlibEnv.Install(env['INSTALL_DIR'], dlib)

class BreakIt(Exception): pass

def WalkDirsForComponents(env, topdir, ignore):
    global isPreProcessing
    global isDetectingDependencies
    global downloadedDependencies
    
    isPreProcessing = True
    # Step 1: populate all the components
    #print 'Step 1'
    for root, dirnames, filenames in os.walk(topdir):
        if ignore.count(os.path.relpath(root,env.Dir('#').abspath)) == 0:
            for filename in fnmatch.filter(filenames, 'SConscript'):
                pathname = os.path.join(root, filename)
                env.SConscript(pathname, exports='env')
            
    # Step 2: verify downloadable dependencies            
    #print 'Step 2'
    downloadedDependencies = True
    sconsPaths = []
    while downloadedDependencies:
        #print 'Step 2-a'
        downloadedDependencies = False
        isDetectingDependencies = True
        del sconsPaths[:]
        try:
            for root, dirnames, filenames in os.walk(topdir):
                if ignore.count(os.path.relpath(root,env.Dir('#').abspath)) == 0:
                    for filename in fnmatch.filter(filenames, 'SConscript'):
                        pathname = os.path.join(root, filename)
                        env.SConscript(pathname, exports='env')
                        sconsPaths.append( (root,lastAddedComponent.name) )
                        if downloadedDependencies:
                            raise BreakIt
        except BreakIt:
            pass
            
        # if something was downloaded, we need to reparse it
        if downloadedDependencies:
            #print 'Step 2-b'
            del sconsPaths[:]
            downloadedDependencies = False
            isDetectingDependencies = False
            for root, dirnames, filenames in os.walk(topdir):
                if ignore.count(os.path.relpath(root,env.Dir('#').abspath)) == 0:
                    for filename in fnmatch.filter(filenames, 'SConscript'):
                        pathname = os.path.join(root, filename)
                        env.SConscript(pathname, exports='env')
                        sconsPaths.append( (root,lastAddedComponent.name) )
            downloadedDependencies = True
           
    # Step 3: real SConscript walk
    #print 'Step 3'
    isDetectingDependencies = False
    isPreProcessing = False
    for (sconsPath,componentName) in sconsPaths:
        variantPath = os.path.join(env['BUILD_DIR'], componentName)
        sconscriptPath = os.path.join(sconsPath,'SConscript')
        env.SConscript(sconscriptPath, variant_dir=variantPath, duplicate=0, exports='env')

