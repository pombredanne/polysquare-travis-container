# /psqtraviscontainer/package_system.py
#
# Implementations of package-system controllers for various distributions.
#
# See LICENCE.md for Copyright information
"""Implementations of package-system controllers for various distributions."""

_UBUNTU_MAIN_ARCHS = ["i386", "amd64"]
_UBUNTU_PORT_ARCHS = ["armhf", "arm64", "powerpc", "ppc64el"]
_UBUNTU_MAIN_ARCHIVE = "http://archive.ubuntu.com/ubuntu/"
_UBUNTU_PORT_ARCHIVE = "http://ports.ubuntu.com/ubuntu-ports/"

import sys

import tempfile

from psqtraviscontainer import directory
from psqtraviscontainer import download

import six

import tempdir

from termcolor import colored


def _run_task(executor, description, argv):
    """Run command through executor argv and prints description."""
    sys.stdout.write(colored("-> {0}\n".format(description), "white"))
    executor.execute_success(argv)


class Dpkg(object):

    """Debian Packaging System."""

    def __init__(self,
                 config,
                 arch,
                 executor):
        """Initialize DpkgPackageSystem with DistroConfig."""
        super(Dpkg, self).__init__()
        self._config = config
        self._arch = arch
        self._executor = executor

    def add_repositories(self, repos):
        """Add a repository to the central packaging system."""
        _ubuntu_urls = [
            (_UBUNTU_MAIN_ARCHS, _UBUNTU_MAIN_ARCHIVE),
            (_UBUNTU_PORT_ARCHS, _UBUNTU_PORT_ARCHIVE)
        ]

        def _format_user_line(line, kwargs):
            """Format a line and turns it into a valid repo line."""
            formatted_line = line.format(**kwargs)  # pylint:disable=W0142
            return "deb {0}".format(formatted_line)

        def _value_or_error(value):
            """Return first item in value, or ERROR if value is empty."""
            return value[0] if len(value) else "ERROR"

        format_keys = {
            "ubuntu": [u[1] for u in _ubuntu_urls if self._arch in u[0]],
            "debian": ["http://ftp.debian.org/"],
            "launchpad": ["http://ppa.launchpad.net/"],
            "release": [self._config.release]
        }
        format_keys = {
            k: _value_or_error(v) for k, v in format_keys.items()
        }

        # We will be creating a bash script each time we need to add
        # a new source line to our sources list and executing that inside
        # the proot. This guaruntees that we'll always get the right
        # permissions.
        with tempfile.NamedTemporaryFile() as bash_script:
            append_lines = [_format_user_line(l, format_keys) for l in repos]
            for count, append_line in enumerate(append_lines):
                path = "/etc/apt/sources.list.d/{0}.list".format(count)
                append_cmd = "echo \"{0}\" > {1}\n".format(append_line, path)
                bash_script.write(six.b(append_cmd))

            bash_script.flush()
            self._executor.execute_success(["bash", bash_script.name])

    def install_packages(self, package_names):
        """Install all packages in list package_names."""
        _run_task(self._executor,
                  "Update repositories",
                  ["apt-get", "update", "-qq", "-y", "--force-yes"])
        _run_task(self._executor,
                  "Install {0}".format(str(package_names)),
                  ["apt-get",
                   "install",
                   "-qq",
                   "-y",
                   "--force-yes"] + package_names)


class Yum(object):

    """RedHat Packaging System."""

    def __init__(self,
                 config,
                 arch,
                 executor):
        """Initialize DpkgPackageSystem with DistroConfig."""
        super(Yum, self).__init__()
        self._config = config
        self._executor = executor

        del arch

    def add_repositories(self, repos):
        """Add a repository to the central packaging system."""
        with tempdir.TempDir() as download_dir:
            with directory.Navigation(download_dir):
                for repo in repos:
                    repo_file = download.download_file(repo)
                    # Create a bash script to copy the downloaded repo file
                    # over to /etc/yum/repos.d
                    with tempfile.NamedTemporaryFile() as bash_script:
                        copy_cmd = ("cp \"{0}\""
                                    "/etc/yum/repos.d").format(repo_file)
                        bash_script.write(six.b(copy_cmd))
                        bash_script.flush()
                        self._executor.execute_success(["bash",
                                                        bash_script.name])

    def install_packages(self, package_names):
        """Install all packages in list package_names."""
        _run_task(self._executor,
                  "Install {0}".format(str(package_names)),
                  ["yum", "install", "-y"] + package_names)
