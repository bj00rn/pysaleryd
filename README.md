![PyPI-Server](https://img.shields.io/pypi/v/pysaleryd.svg)
[![Monthly Downloads](https://pepy.tech/badge/pysaleryd/month)](https://pepy.tech/project/pysaleryd)
[![Project generated with PyScaffold](https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold)](https://pyscaffold.org/)

# pysaleryd

Python library for controlling Saleryd HRV system

Python library for controlling Saleryd HRV system using the built-in websocket server used by the [Saleryd HRV Homeassistant integration](https://github.com/bj00rn/ha-saleryd-ftx).

## Supported devices

| Model                | Supported control system versions | Unsupported control system versions |
|----------------------|-----------------------------------|-------------------------------------|
| LOKE LS-01/LT-01     | 4.1.5                             | <4.1.5                              |
| LOKE LS-02/LT-02     | unknown support                   | unknown support                     |

## Example usage

```python
import asyncio
from pysaleryd.client import Client
from pysaleryd.const import DataKey

def handle_message(data: dict):
    # must be safe to call from event loop
    print("got data: ", data)

def handle_state_change(state):
    # must be safe to call from event loop
    print("new state: ", state)

async def main():
    update_interval = 10
    async with Client(HOST, update_interval=update_interval) as hrv_client:
        hrv_client.add_message_handler(handle_message)
        hrv_client.add_state_change_handler(handle_state_change)
        await asyncio.sleep(update_interval + 1) # wait around a bit for data
        await hrv_client.send_command(DataKey.FIREPLACE_MODE, 1) # turn on fireplace mode

loop = asyncio.new_event_loop()
loop.run_until_complete(main())
```

## Troubleshooting

- Confirm system is connected and UI is reachable on the local network. Follow steps in the manual.
- Confirm websocket port by connecting to the UI using a browser and take note of websocket port using debug console in browser. 3001 is probably default.
- The HRV system can only handle a few connected clients. Shut down any additional clients/browsers sessions and try again.

## Disclaimer

Use at your own risk.

This project is in no way affiliated with the manufacturer.

All product names, logos, and brands are property of their respective owners. All company, product and service names used are for identification purposes only. Use of these names, logos, and brands does not imply endorsement.
