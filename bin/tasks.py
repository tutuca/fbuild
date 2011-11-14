from subprocess import call, check_output
from termcolor import cprint

def dependency_method_wrapper(projects, project, method):
    d = projects.get(project)
    if d:
        d.env = {
                'WS_DIR': 'projects',
                'EXTERNAL_DIR': 'scons/site_scons/external',
                'ROOT': 'scons'
                }
        getattr(d, method)()
    else:
        cprint("Cannot find %s in project file" % project, 'red')

def checkout(project, task, env):
    dependency_method_wrapper(env['projects'], project, 'download')

def update(project, task, env):
    dependency_method_wrapper(env['projects'], project, 'update')

def astyle(project, task, env):
    version = float(check_output('astyle -V 2>&1 | cut -f4 -d" "', shell=True))
    if version >= 1.24:
        cmd = 'cd projects; cd ' + project + '; astyle -k1 --recursive --options=none --convert-tabs -bSKpUH *.h *.cpp'
        call(cmd, shell=True)
    else:
        cprint("Astyle version should be >=1.24", 'red')

tasks = {
        'checkout': checkout,
        'astyle'  : astyle,
        'update'  : update
        }
