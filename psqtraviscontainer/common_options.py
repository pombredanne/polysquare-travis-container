# /psqtraviscontainer/common_options.py
#
# Options common to both both commands.
#
# See LICENCE.md for Copyright information
"""Options common to both both commands."""

import platform

import configargparse

from psqtraviscontainer import architecture
from psqtraviscontainer import distro


def get_parser(action):
    """Get a parser with options common to both commands."""
    # Iterate over the AVAILABLE_DISTRIBUTIONS and get a list of available
    # distributions and architecutres for the --distro and --arch arguments
    available_architectures = set()
    available_distributions = set()

    for distribution in distro.AVAILABLE_DISTRIBUTIONS:
        available_distributions.add(distribution.type)

        for arch in distribution.archs:
            available_architectures.add(architecture.Alias.universal(arch))

    description = "{0} a Travis CI container".format(action)
    parser = configargparse.ArgumentParser(description=description)

    current_arch = architecture.Alias.universal(platform.machine())

    parser.add_argument("containerdir",
                        nargs=1,
                        metavar=("CONTAINER_DIRECTORY"),
                        help="Directory to place container in",
                        type=str)
    parser.add_argument("--distro",
                        nargs=1,
                        type=str,
                        help="Distribution name to create container of",
                        choices=available_distributions,
                        env_var="CONTAINER_DISTRO")
    parser.add_argument("--release",
                        nargs=1,
                        type=str,
                        help="Distribution release to create container of",
                        env_var="CONTAINER_RELEASE")
    parser.add_argument("--arch",
                        nargs=1,
                        type=str,
                        help=("Architecture (all architectures other than "
                              "the system architecture will be emulated with "
                              "qemu)"),
                        default=[current_arch],
                        choices=available_architectures,
                        env_var="CONTAINER_ARCH")

    return parser
