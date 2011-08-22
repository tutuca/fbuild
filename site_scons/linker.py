import platform

def loadLinkOptions(env):
    (arch,binType) = platform.architecture()
    # Resolve the rpath so everything works smooth from
    # the install dir. This makes easier to deploy somewhere
    # else, you only need to pass INSTALL_<BIN/LIB/HEADERS>_DIR parameters to 
    # scons to deploy it somewhere else
    env.Append( RPATH = env['INSTALL_HEADERS_DIR'])
    env.Append( RPATH = env['INSTALL_LIB_DIR'])
    env['ENV']['LD_LIBRARY_PATH'] = env['INSTALL_LIB_DIR'] 

