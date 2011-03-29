# FuDePan boilerplate required here

# This file contains wrappers to the creation of the different component types
# this way we can improve the parameters and unify them

def CreateProgram(env, name, src):
    program = env.Program(name, src)
    env.Install(env['INSTALL_DIR'], program)


