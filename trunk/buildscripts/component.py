# FuDePan boilerplate required here

# This file contains wrappers to the creation of the different component types
# this way we can improve the parameters and unify them
import os

def CreateProgram(env, name, src, deps):
    libPaths = []
    # we have to add all build paths because the build path could
    # be different to the dependency
    for root, dirnames, filenames in os.walk(env['BUILD_DIR']):
        for dirname in dirnames:
            libPaths.append(os.path.join(root,dirname))
    print libPaths
    program = env.Program(name, src, LIBS=deps, LIBPATH=libPaths)
    env.Install(env['INSTALL_DIR'], program)

def CreateStaticLibrary(env, name, src):
    lib = env.Library(name, src)

def CreateSharedLibrary(env, name, src):
    dlib = env.SharedLibrary(name, src)
    env.Install(env['INSTALL_DIR'], dlib)
