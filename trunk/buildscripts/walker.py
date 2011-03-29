# FuDePan boilerplate required here

import fnmatch
import os

def WalkDirsForSConscript(env, topdir):
    matches = []
    for root, dirnames, filenames in os.walk(topdir):
        for filename in fnmatch.filter(filenames, 'SConscript'):
            env.SConscript(os.path.join(root, filename), variant_dir=env['BUILD_DIR'], duplicate=0, exports='env')
