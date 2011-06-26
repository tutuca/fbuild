import platform

def loadLinuxCompilerOptions(env):
	# common options
	commonFlags = [
    	'-Wall',
        '-Wextra',
        '-pedantic'
		]
	env.Append(CXXFLAGS = commonFlags, CFLAGS = commonFlags)
	# Options for 64bit archs
	(arch,binType) = platform.architecture()
	if arch == '64bit':
		env.Append(CXXFLAGS = '-fPIC', CFLAGS = '-fPIC')
	# build type options
	if env.GetOption('type') == 'dbg':
		dbgFlags = [
			'-ggdb3'
			]
		env.Append(CXXFLAGS = dbgFlags, CFLAGS = dbgFlags)
		env.Append(CPPDEFINES = ['DEBUG'])
	elif env.GetOption('type') == 'opt':
		optFlags = [
			'-O3'
		]
		env.Append(CXXFLAGS = optFlags, CFLAGS = optFlags)
		env.Append(CPPDEFINES = ['NDEBUG'])
	if env.GetOption('effective'):
		env.Append(CXXFLAGS = '-Weffc++', CFLAGS = '-Weffc++')

def loadCompilerOptions(env):
    (arch,binType) = platform.architecture()
    if binType == 'ELF':
        loadLinuxCompilerOptions(env)

    

