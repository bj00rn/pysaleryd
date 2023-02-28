"""
This is a skeleton file that can serve as a starting point for a Python
console script. To run this script uncomment the following lines in the
``[options.entry_points]`` section in ``setup.cfg``::

    console_scripts =
         pysaleryd = pysaleryd.skeleton:run

Then run ``pip install .`` (or ``pip install -e .`` for editable mode)
which will install the command ``pysaleryd`` inside your current environment.

Besides console scripts, the header (i.e. until ``_logger``...) of this file can
also be used as template for Python modules.

Note:
    This file can be renamed depending on your needs or safely removed if not needed.

References:
    - https://setuptools.pypa.io/en/latest/userguide/entry_point.html
    - https://pip.pypa.io/en/stable/reference/pip_install
"""

import argparse
import asyncio
import logging
import signal
import sys

import aiohttp

from pysaleryd import __version__
from pysaleryd.client import Client

__author__ = "Björn Dalfors"
__copyright__ = "Björn Dalfors"
__license__ = "MIT"

_logger = logging.getLogger(__name__)

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
    parser = argparse.ArgumentParser(description=f"Saleryd HRV Client {__version__}")
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
    listen = parser.add_argument_group()
    listen.add_argument("--listen", action="store_true", help="print incoming messages")
    listen.add_argument(
        "-t", dest="timeout", help="listen timeout", type=int, metavar="INT", default=5
    )
    send = parser.add_argument_group()
    send.add_argument("--send", action="store_true", help="send command to the system")
    send.add_argument("--key", type=str, dest="send_key", help="command key")
    send.add_argument("--data", type=str, dest="send_data", help="command data")

    return parser.parse_args(args)


def setup_logging(loglevel: int):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )


def signal_handler(signum: int, frame):
    """Signal handler"""
    _logger.debug("Received signal %s, exiting..", signum)
    sys.exit(0)


def main(args):
    """Main program"""
    args = parse_args(args)
    setup_logging(args.loglevel)

    signal.signal(signal.SIGINT, signal_handler)

    async def runner(args):
        async with aiohttp.ClientSession() as session:
            async with Client(args.host, args.port, session) as hrv_client:
                if args.send:
                    if not isinstance(args.send_key, str):
                        raise Exception("Invalid key supplied")
                    if not isinstance(args.send_data, str):
                        raise Exception("Invalid data supplied")
                    await hrv_client.send_command(args.send_key, args.send_data)
                if args.listen:
                    await asyncio.sleep(args.timeout)
                    print(hrv_client.data)

    asyncio.run(runner(args))


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
