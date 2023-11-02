"""Install a blender plugin with a command line interface.

>>> xf-install-plugin --help
>>> xf-render {} [-o {output_path}]
"""

from pathlib import Path
from textwrap import dedent

from typer import Argument, Option, Typer
from typing_extensions import Annotated

import xrfeitoria as xf
from xrfeitoria.utils.tools import Logger

app = Typer(pretty_exceptions_show_locals=False)


@app.command()
def main(
    # path config
    plugin_path: Annotated[
        Path,
        Argument(
            ...,
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
            help='filepath of the mesh to be renderer',
        ),
    ],
    plugin_name_blender: Annotated[
        str,
        Option(
            '--plugin-name-blender',
            '-n',
            help='name of the plugin in blender',
        ),
    ] = None,
    # engine config
    blender_exec: Annotated[
        Path,
        Option('--blender-exec', help='path to blender executable, e.g. /usr/bin/blender'),
    ] = None,
    # misc
    debug: Annotated[
        bool,
        Option('--debug/--no-debug', help='log in debug mode'),
    ] = False,
):
    """Install a blender plugin with a command line interface."""
    logger = Logger.setup_logging(level='DEBUG' if debug else 'INFO')
    logger.info(
        dedent(
            f"""\
            :rocket: Starting:
            Executing install plugin with the following parameters:
            ---------------------------------------------------------
            [yellow]# path config[/yellow]
            - plugin_path: {plugin_path}
            - plugin_name_blender: {plugin_name_blender}
            [yellow]# engine config[/yellow]
            - blender_exec: {blender_exec}
            [yellow]# misc[/yellow]
            - debug: {debug}
            ---------------------------------------------------------"""
        )
    )

    with xf.init_blender(exec_path=blender_exec, background=True) as xf_runner:
        xf_runner.utils.install_plugin(plugin_path, plugin_name_blender)

    logger.info(':tada: [green]Installation of plugin completed![/green]')


if __name__ == '__main__':
    app()
