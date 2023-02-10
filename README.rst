.. These are examples of badges you might want to add to your README:
   please update the URLs accordingly

    .. image:: https://api.cirrus-ci.com/github/<USER>/pysaleryd.svg?branch=main
        :alt: Built Status
        :target: https://cirrus-ci.com/github/<USER>/pysaleryd
    .. image:: https://readthedocs.org/projects/pysaleryd/badge/?version=latest
        :alt: ReadTheDocs
        :target: https://pysaleryd.readthedocs.io/en/stable/
    .. image:: https://img.shields.io/coveralls/github/<USER>/pysaleryd/main.svg
        :alt: Coveralls
        :target: https://coveralls.io/r/<USER>/pysaleryd
    .. image:: https://img.shields.io/pypi/v/pysaleryd.svg
        :alt: PyPI-Server
        :target: https://pypi.org/project/pysaleryd/
    .. image:: https://img.shields.io/conda/vn/conda-forge/pysaleryd.svg
        :alt: Conda-Forge
        :target: https://anaconda.org/conda-forge/pysaleryd
    .. image:: https://pepy.tech/badge/pysaleryd/month
        :alt: Monthly Downloads
        :target: https://pepy.tech/project/pysaleryd
    .. image:: https://img.shields.io/twitter/url/http/shields.io.svg?style=social&label=Twitter
        :alt: Twitter
        :target: https://twitter.com/pysaleryd

.. image:: https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold
    :alt: Project generated with PyScaffold
    :target: https://pyscaffold.org/

|

=========
pysaleryd
=========


    Python library for controlling Saleryd HRV system


Python library for controlling Saleryd HRV system using the built in websocket server used by Saleryd HRV Homeassistant integration https://github.com/bj00rn/ha-saleryd-ftx


Supported devices
==================

LOKE1/Loke Basic/LS-01 using control system 4.1.1

Usage with asyncio as library
=============================


.. code-block:: python3

    from pysaleryd.client import Client
    client = Client(WEBSOCKET_URL, WEBSOCKET_PORT)
    await client.connect()
    await asyncio.sleep(2)
    print(data) # prints buffered data from system

CLI usage
=========

Connect to system and capture websocket data to stdout

.. code-block:: shell

    $ ./pysaleryd --host [WEBSOCKET_URL] --port [WEBSOCKET_PORT]

Troubleshooting
===============
* Confirm system is connected and UI is reachable on the local network. Follow steps in the manual.
* Confirm websocket port by connecting to the UI using a browser and take note of websocket port using debug console in browser. 3001 is probably default
* The system HRV system can only handle a few connected clients. Shut down any additional clients/browsers and try again


Disclaimer
==========

Use at own risk.

This project is in no way affiliated with the manufacturer. 

All product names, logos, and brands are property of their respective owners. All company, product and service names used are for identification purposes only. Use of these names, logos, and brands does not imply endorsement.

.. _pyscaffold-notes:

Note
====

This project has been set up using PyScaffold 4.4. For details and usage
information on PyScaffold see https://pyscaffold.org/.
