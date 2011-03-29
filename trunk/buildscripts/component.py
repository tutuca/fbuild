# FuDePan boilerplate required here

# This file contains wrappers to the creation of the different component types
# this way we can improve the parameters and unify them

def CreateProgram(env, name, src):
    program = env.Program(name, src)
    env.Install(env['INSTALL_DIR'], program)

def CreateStaticLibrary(env, name, src):
    lib = env.Library(name, src)

def CreateSharedLibrary(env, name, src):
    dlib = env.SharedLibrary(name, src)
    env.Install(env['INSTALL_DIR'], dlib)
