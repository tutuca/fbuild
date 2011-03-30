# FuDePan boilerplate required here

import fnmatch
import os
import SCons

components = {}
isPreProcessing = False

class Component(object):
    def __init__(self, name, buildDir, incDirs):
        global components
        self.name = name
        self.buildDir = buildDir
        self.incDirs = incDirs
    def __hash__(self):
        self.name.__hash__()
    def __eq__(self,other):
        return self.name == other

def AddComponent(env, name, buildDir, incDirs):
    global components
    if components.has_key(name) and components[name] is not None:
        raise Exception('Component already defined: %s' % name)
    components[name] = Component(name, buildDir, incDirs)

# This two functions have to solve recursively the dependencies
# right now is just one-level

def GetIncludePaths(env, deps):
    incpaths = []
    for dep in deps:
        incpaths.append(components[dep].incDirs.get_abspath())
    return incpaths

def GetLibPaths(env, deps):
    libpaths = []
    # we have to add all build paths because the variant dir depends
    # on the name of the folder instead of the name of the component
    # TODO: do something smartert with the 'components' variable
    for root, dirnames, filenames in os.walk(env['BUILD_DIR']):
        for dirname in dirnames:
	    libpaths.append(os.path.join(root,dirname))
    return libpaths

def CreateProgram(env, name, inc, src, deps):
    if isPreProcessing == True:
        AddComponent(env, name, '', inc)
    else: 
        incpaths = GetIncludePaths(env, deps)
        incpaths.append(inc.get_abspath())
        libpaths = GetLibPaths(env, deps)
        program = env.Program(name, src, CPPPATH=incpaths, LIBS=deps, LIBPATH=libpaths)
        env.Install(env['INSTALL_DIR'], program)
   
def CreateStaticLibrary(env, name, inc, src, deps):
    if isPreProcessing == True:
        AddComponent(env, name, '', inc)
    else: 
        incpaths = GetIncludePaths(env, deps)
        incpaths.append(inc.get_abspath())
        libpaths = GetLibPaths(env, deps)  
        lib = env.Library(name, src, CPPPATH=incpaths)

def CreateSharedLibrary(env, name, inc, src, deps):
    if isPreProcessing == True:
        AddComponent(env, name, '', inc)
    else:
        incpaths = GetIncludePaths(env, deps)
        incpaths.append(inc.get_abspath())
        libpaths = GetLibPaths(env, deps)  
        dlib = env.SharedLibrary(name, src, CPPPATH=incpaths, LIBS=deps, LIBPATH=libpaths)
        env.Install(env['INSTALL_DIR'], dlib)

def WalkDirsForComponents(env, topdir):
    global isPreProcessing
    sconscriptspath = []
    isPreProcessing = True
    wspath = SCons.Node.FS.default_fs.pathTop
    for root, dirnames, filenames in os.walk(topdir):
        for filename in fnmatch.filter(filenames, 'SConscript'):
            (headPath,tailPath)=os.path.split(root)
            pathname = os.path.join(root, filename)
            variantPath = os.path.join(env['BUILD_DIR'], tailPath)
            env.SConscript(pathname, variant_dir=variantPath, duplicate=0, exports='env')
    isPreProcessing = False
    for root, dirnames, filenames in os.walk(topdir):
        for filename in fnmatch.filter(filenames, 'SConscript'):
            (headPath,tailPath)=os.path.split(root)
            pathname = os.path.join(root, filename)
            variantPath = os.path.join(env['BUILD_DIR'], tailPath)
            env.SConscript(pathname, variant_dir=variantPath, duplicate=0, exports='env')

