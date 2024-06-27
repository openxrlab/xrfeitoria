import os
import subprocess


def main(port: int = 50001):
    if os.name == 'nt':
        port_cmd = f'set BLENDER_PORT={port}'
    else:
        port_cmd = f'BLENDER_PORT={port}'

    cmds = [
        port_cmd,
        '&&',
        'python',
        '-c',
        '"import xrfeitoria as xf; xf.init_blender(background=True).close()"',
    ]
    cmd = ' '.join(cmds)
    print(cmd)
    p = subprocess.Popen(cmd, shell=True)


if __name__ == '__main__':
    main(50000)
    main(50001)
    main(50002)
    main(50003)
