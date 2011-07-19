import platform

def loadLinkOptions(env):
    (arch,binType) = platform.architecture()
    # Resolve the rpath so everything works smooth from
    # the install dir. This makes easier to deploy somewhere
    # else, you only need to pass INSTALL_DIR parameter to 
    # scons to deploy it somewhere else
    env.Append( RPATH = env['INSTALL_DIR'])
    env['ENV']['LD_LIBRARY_PATH'] = env['INSTALL_DIR'] 

