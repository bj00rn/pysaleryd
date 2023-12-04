"""Websocket server for testing"""

import asyncio
import logging

import aiohttp
from aiohttp import web
from aiohttp.web import WebSocketResponse
from aiohttp.web_request import Request

_LOGGER = logging.getLogger(__name__)


class WebsocketView(web.View):
    def __init__(self, request: Request) -> None:
        self.receive = asyncio.queues.Queue()
        self.send = asyncio.queues.Queue()
        self._message_handler = None
        self._outgoing_message_handler = None
        self.stream_handler = None
        self._listener = None
        self._pinger = None
        super().__init__(request)

    @classmethod
    async def cleanup(cls, ws):
        """Close websocket connection"""
        await ws.close(code=aiohttp.WSCloseCode.GOING_AWAY, message="Server shutdown")

    async def pinger(self):
        """Send ping to peer"""
        while True:
            await asyncio.sleep(30)
            await self.send.put("PING")

    async def data_generator(self):
        """Generate data and push to queue"""
        while True:
            await self.send.put("#MF: 1+ 1+ 1+1")
            await asyncio.sleep(0.5)

    async def outgoing_message_handler(self, ws: WebSocketResponse):
        """Send outgoing messages to peer"""
        while True:
            msg = await self.send.get()
            await ws.send_str(msg)

    async def incoming_message_handler(self):
        """Handle incoming messages"""
        while True:
            msg = await self.receive.get()  # noqa: F841
            if not self.stream_handler:
                self.stream_handler = asyncio.create_task(self.data_generator())

    async def listener(self, ws: WebSocketResponse):
        """Push incoming messages to queue"""
        try:
            while True:
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        await self.receive.put(msg)
        finally:
            task = asyncio.create_task(self.cleanup(ws), name="Cleanup")
            await asyncio.shield(task)

    async def websocket_handler(self, request):
        """Websocket handler"""
        ws = aiohttp.web.WebSocketResponse()
        await ws.prepare(request)
        self._message_handler = asyncio.create_task(self.incoming_message_handler())
        self._outgoing_message_handler = asyncio.create_task(
            self.outgoing_message_handler(ws)
        )
        self._pinger = asyncio.create_task(self.pinger())
        self._listener = asyncio.create_task(self.listener(ws), name="Serve")
        await self._listener
        return ws

    async def get(self):
        """GET
        Serve websocket
        """
        return await self.websocket_handler(self.request)


def run_server(argv):  # pylint: disable W0613
    """Init function when running from cli
    See https://docs.aiohttp.org/en/stable/web_quickstart.html#command-line-interface-cli # noqa: E501
    """
    app = web.Application()
    app.router.add_view("/", WebsocketView)
    return app
