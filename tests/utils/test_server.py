#!/usr/bin/env python

import asyncio
import logging

from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosed

_LOGGER = logging.getLogger(__name__)


async def data_generator(ws: ServerConnection):
    """Generate data and push to queue"""
    while True:
        try:
            await ws.send("#MF: 1+ 1+ 1+1")
            await asyncio.sleep(0.5)
        except ConnectionClosed:
            break


class TestServer:
    async def _handler(self, websocket: ServerConnection):
        """Websocket handler to emulate HRV"""
        message = await websocket.recv()
        _LOGGER.debug("Received %s", message)
        await asyncio.gather(asyncio.create_task(data_generator(websocket)))

    def __init__(self, host, port):
        self.port = port
        self.host = host
        self._stop = None
        self._server = None
        self._gen = None

    def stop(self):
        """Stop server"""
        if self._server:
            self._server.close()
            # self._stop.cancel()

    async def start(self):
        """Start server"""
        self._server = await serve(
            self._handler, self.host, self.port, start_serving=True
        )
        # self._stop = asyncio.create_task(self._server.serve_forever())

    async def __aenter__(self, *args, **kwargs):
        await self.start()
        return self

    async def __aexit__(self, *args, **kwargs):
        self.stop()
