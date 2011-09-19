# based on: http://xtargets.com/2010/04/21/recursive-install-builder-for-scons/

import os

def recursive_install(env, path ):
    nodes = env.Glob(os.path.join(path, '*'), strings=False)
    nodes.extend(env.Glob(os.path.join(path, '*.*'), strings=False))
    out = []
    for n in nodes:
        if n.isdir():
            out.extend( recursive_install(env, n.abspath ))
        else:
            out.append(n)

    return out

def RecursiveInstall(env, target, dir):
    nodes = recursive_install(env, dir)

    dir = os.path.split(env.Dir(dir).abspath)[0]
    target = env.Dir(target).abspath

    l = len(dir) + 1
    relnodes = [ n.abspath[l:] for n in nodes ]

    for n in relnodes:
        t = os.path.join(target, n)
        s = os.path.join(dir, n)
        env.Alias('install', env.InstallAs(env.File(t), env.File(s)))
