"""
This is a skeleton file that can serve as a starting point for a Python
console script. To run this script uncomment the following lines in the
``[options.entry_points]`` section in ``setup.cfg``::

    console_scripts =
         pysaleryd = pysaleryd.skeleton:run

Then run ``pip install .`` (or ``pip install -e .`` for editable mode)
which will install the command ``fibonacci`` inside your current environment.

Besides console scripts, the header (i.e. until ``_logger``...) of this file can
also be used as template for Python modules.

Note:
    This file can be renamed depending on your needs or safely removed if not needed.

References:
    - https://setuptools.pypa.io/en/latest/userguide/entry_point.html
    - https://pip.pypa.io/en/stable/reference/pip_install
"""

import argparse
import logging
import sys
import asyncio
import signal

from aiohttp import ClientSession

from pysaleryd import __version__
from pysaleryd.client import Client

__author__ = "Björn Dalfors"
__copyright__ = "Björn Dalfors"
__license__ = "MIT"

_logger = logging.getLogger(__name__)


# ---- Python API ----
# The functions defined in this section can be imported by users in their
# Python scripts/interactive interpreter, e.g. via
# `from pysaleryd.skeleton import fib`,
# when using this Python module as a library.


# ---- CLI ----
# The functions defined in this section are wrappers around the main Python
# API allowing them to be called directly from the terminal as a CLI
# executable/script.


def parse_args(args):
    """Parse command line parameters

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--help"]``).

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(description="Just a Fibonacci demonstration")
    parser.add_argument(
        "--version",
        action="version",
        version=f"pysaleryd {__version__}",
    )
    parser.add_argument(
        "--port", dest="port", help="port number", type=int, metavar="INT", required=True
    )
    parser.add_argument("--host", dest="host", help="host", type=str, required=True)
    parser.add_argument(
        "-t", dest="timeout", help="timeout", type=int, metavar="INT", default=None
    )

    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO,
    )
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="loglevel",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )

    parser.add_argument("--send", dest="data", type=str, help="command to send to the system")

    return parser.parse_args(args)


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )


def signal_handler(signum, frame):
    """Signal handler"""
    _logger.debug("Received signal %s, exiting..", signum)
    sys.exit(0)


def main(args):
    """Main program"""
    args = parse_args(args)
    setup_logging(args.loglevel)

    signal.signal(signal.SIGINT, signal_handler)

    def handle_data(data=None):
        if data:
            print(data)

    async def listen(host, port, timeout):
        async with ClientSession() as session:
            client = Client(host, port, session)
            client.add_handler(handle_data)
            await client.connect()
            if timeout:
                await asyncio.sleep(timeout)
            else:
                while True:
                    await asyncio.sleep(0)

    asyncio.run(listen(args.host, args.port, args.timeout))


def run():
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    # ^  This is a guard statement that will prevent the following code from
    #    being executed in the case someone imports this file instead of
    #    executing it as a script.
    #    https://docs.python.org/3/library/__main__.html

    # After installing your project with pip, users can also run your Python
    # modules as scripts via the ``-m`` flag, as defined in PEP 338::
    #
    #     python -m pysaleryd.skeleton
    #
    run()
