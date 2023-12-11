
.. image:: https://img.shields.io/pypi/v/pysaleryd.svg
    :alt: PyPI-Server
    :target: https://pypi.org/project/pysaleryd/
.. image:: https://pepy.tech/badge/pysaleryd/month
    :alt: Monthly Downloads
    :target: https://pepy.tech/project/pysaleryd

.. image:: https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold
    :alt: Project generated with PyScaffold
    :target: https://pyscaffold.org/

|

=========
pysaleryd
=========


    Python library for controlling Saleryd HRV system


Python library for controlling Saleryd HRV system using the built in websocket server used by Saleryd HRV Homeassistant integration https://github.com/bj00rn/ha-saleryd-ftx

Maintains a reconnecting websocket to the system.

Supported devices
==================

LOKE1/Loke Basic/LS-01 using control system 4.1.5

Usage with asyncio as library
=============================


Read data
---------

.. code-block:: python3

    import asyncio
    import aiohttp

    from pysaleryd.client import Client

    async with aiohttp.ClientSession() as session:
        async with Client(WEBSOCKET_URL, WEBSOCKET_PORT, session) as hrv_client:
            await asyncio.sleep(2) # wait a bit for some data
            print(client.data)

Read data using callback
------------------------

.. code-block:: python3

    import asyncio
    import aiohttp

    from pysaleryd.client import Client

    def handle_message(data: dict):
        print(data)

    update_interval = 10 # call handle_message every 30 seconds

    async with aiohttp.ClientSession() as session:
        async with Client(WEBSOCKET_URL, WEBSOCKET_PORT, session, update_interval) as hrv_client:
            hrv_client.add_handler(handle_message)
            await asyncio.sleep(update_interval +1 ) # wait around a bit for data

Send control command
--------------------
Command syntax can be found by dissecting websocket messages in the built in web ui

.. code-block:: python3

    import asyncio
    import aiohttp

    from pysaleryd.client import Client

    async with aiohttp.ClientSession() as session:
        async with Client(WEBSOCKET_URL, WEBSOCKET_PORT, session) as hrv_client:
            await hrv_client.send_command("XX", 1)

Troubleshooting
===============
* Confirm system is connected and UI is reachable on the local network. Follow steps in the manual.
* Confirm websocket port by connecting to the UI using a browser and take note of websocket port using debug console in browser. 3001 is probably default
* The system HRV system can only handle a few connected clients. Shut down any additional clients/browsers sessions and try again.


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
