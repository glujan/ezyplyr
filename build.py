import os
from functools import partial

from pip.commands.install import InstallCommand
from pip.commands.wheel import WheelCommand
from pybuilder.core import use_plugin, init, task, description, depends


use_plugin("python.core")
use_plugin("python.flake8")
use_plugin("python.distutils")
use_plugin("copy_resources")


name = "ezyplyr"
default_task = "publish"


@init
def set_properties(project):
    wheelhouse = 'lib'
    project.depends_on_requirements("requirements.txt")


    project.set_property('dir_source_main_python', 'src/main')
    project.set_property('dir_source_main_scripts', 'src/scripts')
    project.set_property('wheelhouse', wheelhouse)
    project.set_property('copy_resources_target', '$dir_target')
    project.set_property('copy_resources_glob', [os.path.join(wheelhouse, '**.whl')])


@task
@description('Download needed modules as wheel packages')
def download_dependencies(project):
    wheelhouse = project.get_property('wheelhouse')

    command = WheelCommand()
    args = [
        '-r', 'requirements.txt',
        '--wheel-dir={}'.format(wheelhouse)
    ]

    opts, args = command.parse_args(args)
    command.run(opts, args)


@task
@description('Install dependencies')
@depends('download_dependencies')
def install_requirements(project):
    wheelhouse = project.get_property('wheelhouse')
    prepand_wheelhouse_dir = partial(os.path.join, wheelhouse)

    command = InstallCommand()
    args = ['--force-reinstall',
            '--ignore-installed',
            '--upgrade',
            '--no-index',
            '--use-wheel',
            '--no-deps',
            ]

    wheels = os.listdir(wheelhouse)
    wheels = map(prepand_wheelhouse_dir, wheels)
    args.extend(wheels)

    opts, args = command.parse_args(args)
    command.run(opts, args)
