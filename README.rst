
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

Example usage
=============================
.. code-block:: python3

    import asyncio

    from pysaleryd.client import Client
    from pysaleryd.const import DataKey

    def handle_message(data: dict):
        # must be safe to call from event loop
        print("message handler")
        print(data)

    async def main():
        update_interval = 10
        with Client("192.168.1.151", update_interval=update_interval) as hrv_client:
            hrv_client.add_message_handler(handle_message)
            await asyncio.sleep(update_interval +1 ) # wait around a bit for data
            await hrv_client.send_command(DataKey.FIREPLACE_MODE, 1) # turn on fireplace mode

    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())

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
