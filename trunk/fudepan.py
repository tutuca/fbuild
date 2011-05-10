
def setDefines(env): 
	env.AppendUnique(CPPFLAGS = ['-DMILI_NAMESPACE'])
	
	# this defines are only for playing with ANA
	#env.AppendUnique(CPPFLAGS = ['-Dmiddleware=ana'])
	#env.AppendUnique(CPPFLAGS = ['-Dapps=ON'])
