from subprocess import call, check_output
from termcolor import cprint

def checkout(project, task, env):
    d = env['projects'].get(project)
    if d:
        d.env = {
                'WS_DIR': 'projects',
                'EXTERNAL_DIR': 'scons/site_scons/external',
                'ROOT': 'scons'
                }
        d.download()
    else:
        cprint("Cannot find %s in project file" % project, 'red')

def astyle(project, task, env):
    version = float(check_output('astyle -V 2>&1 | cut -f4 -d" "', shell=True))
    if version >= 1.24:
        cmd = 'cd projects; cd ' + project + '; astyle -k1 --recursive --options=none --convert-tabs -bSKpUH *.h *.cpp'
        call(cmd, shell=True)
    else:
        cprint("Astyle version should be >=1.24", 'red')

tasks = {
        'checkout': checkout,
        'astyle'  : astyle
        }
