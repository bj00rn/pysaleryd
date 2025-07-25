#!/usr/bin/env python

import asyncio
import logging

from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosed

from pysaleryd.helpers.task import task_manager

_LOGGER = logging.getLogger(__name__)


async def data_generator(ws: ServerConnection) -> None:
    """Generate data and push to queue"""
    while True:
        try:
            await ws.send("#MF: 1+ 1+ 1+1")
            await asyncio.sleep(0.5)
        except ConnectionClosed:
            break


class TestServer:
    """Test server"""

    async def _handler(self, websocket: ServerConnection) -> None:
        """Websocket handler to emulate HRV"""
        async with task_manager(cancel_on_exit=True) as task_list:
            message = await websocket.recv()
            _LOGGER.debug("Received %s", message)
            task = self._loop.create_task(
                data_generator(websocket), name="data_generator"
            )
            task_list.add(task)
            await task_list.wait()

    def __init__(self, host, port, loop=None) -> None:
        self.port = port
        self.host = host
        self._stop = None
        self._server: asyncio.Server
        self._gen = None
        self._loop = loop if loop is not None else asyncio.get_running_loop()

    async def close(self) -> None:
        """Stop server"""
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    async def start(self) -> None:
        """Start server"""
        self._server = await serve(
            self._handler, self.host, self.port, start_serving=True
        )

    async def __aenter__(self, *args, **kwargs) -> "TestServer":
        await self.start()
        return self

    async def __aexit__(self, *args, **kwargs) -> None:
        await self.close()
