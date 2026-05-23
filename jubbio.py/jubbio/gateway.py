from __future__ import annotations
import asyncio
import json
import logging
from typing import TYPE_CHECKING, Optional

import aiohttp

from .errors import GatewayError, InvalidToken

if TYPE_CHECKING:
    from .client import Client

log = logging.getLogger(__name__)

GATEWAY_URL = "wss://realtime.jubbio.com/ws/bot"
RECONNECTABLE_CLOSE_CODES = {4000, 4001, 4002, 4003}
FATAL_CLOSE_CODES = {4004}


class Gateway:

    def __init__(self, client: "Client", token: str):
        self._client = client
        self._token = token
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._reconnect_count = 0
        self._max_reconnects = 5
        self._closed = False
        self._ready = asyncio.Event()

    @property
    def is_connected(self) -> bool:
        return self._ws is not None and not self._ws.closed

    async def connect(self):
        self._closed = False
        self._reconnect_count = 0
        await self._connect()

    async def _connect(self):
        try:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession()

            self._ws = await self._session.ws_connect(
                GATEWAY_URL,
                headers={"Authorization": f"Bot {self._token}"},
                heartbeat=30.0,
            )

            await self._identify()
            self._receive_task = asyncio.create_task(self._receive_loop())

        except Exception as e:
            log.error("Gateway bağlantı hatası: %s", e)
            await self._try_reconnect()

    async def _identify(self):
        identify_data = {"token": self._token}
        if hasattr(self._client, "intents") and self._client.intents:
            identify_data["intents"] = self._client.intents.value

        await self._send({"op": 2, "d": identify_data})

    async def _send(self, data: dict):
        if self._ws and not self._ws.closed:
            await self._ws.send_json(data)

    async def _receive_loop(self):
        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self._handle_message(json.loads(msg.data))
                elif msg.type == aiohttp.WSMsgType.BINARY:
                    await self._handle_message(json.loads(msg.data))
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    log.error("WebSocket hatası: %s", self._ws.exception())
                    break
                elif msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.CLOSED):
                    break
        except asyncio.CancelledError:
            return
        except Exception as e:
            log.error("Receive loop hatası: %s", e)

        if not self._closed:
            close_code = self._ws.close_code if self._ws else None
            await self._handle_close(close_code)

    async def _handle_message(self, data: dict):
        op = data.get("op")
        event_type = data.get("t")
        event_data = data.get("d", {})

        if op == 11:
            return

        if op == 10:
            interval = event_data.get("heartbeat_interval", 30000) / 1000
            self._start_heartbeat(interval)
            return

        if op == 0 and event_type:
            await self._dispatch_event(event_type, event_data)

    async def _dispatch_event(self, event_type: str, data: dict):
        event_map = {
            "READY": "on_ready",
            "MESSAGE_CREATE": "on_message",
            "INTERACTION_CREATE": "on_interaction",
            "GUILD_CREATE": "on_guild_join",
            "GUILD_DELETE": "on_guild_remove",
            "GUILD_BAN_ADD": "on_member_ban",
            "GUILD_BAN_REMOVE": "on_member_unban",
            "INVITE_CREATE": "on_invite_create",
            "INVITE_DELETE": "on_invite_delete",
            "PRESENCE_UPDATE": "on_presence_update",
            "GUILD_MEMBER_ADD": "on_member_join",
            "GUILD_MEMBER_REMOVE": "on_member_remove",
        }

        if event_type == "READY":
            self._ready.set()
            self._reconnect_count = 0
            if hasattr(self._client, "_handle_ready"):
                await self._client._handle_ready(data)
            return

        handler_name = event_map.get(event_type)
        if handler_name and hasattr(self._client, "_dispatch"):
            await self._client._dispatch(handler_name, data)

    def _start_heartbeat(self, interval: float):
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop(interval))

    async def _heartbeat_loop(self, interval: float):
        try:
            while not self._closed and self.is_connected:
                await self._send({"op": 1, "d": None})
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            log.error("Heartbeat hatası: %s", e)

    async def _handle_close(self, code: int = None):
        if code in FATAL_CLOSE_CODES:
            self._closed = True
            raise InvalidToken("Geçersiz bot token'ı!")

        if code in RECONNECTABLE_CLOSE_CODES or code is None:
            await self._try_reconnect()

    async def _try_reconnect(self):
        if self._closed:
            return

        if self._reconnect_count >= self._max_reconnects:
            self._closed = True
            raise GatewayError(f"Gateway'e {self._max_reconnects} denemeden sonra bağlanılamadı", code=None)

        self._reconnect_count += 1
        wait_time = min(2 ** self._reconnect_count, 60)
        log.warning("Yeniden bağlanma %d/%d - %ds bekleniyor...", self._reconnect_count, self._max_reconnects, wait_time)
        await asyncio.sleep(wait_time)
        await self._cleanup()
        await self._connect()

    async def _cleanup(self):
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
        if self._ws and not self._ws.closed:
            await self._ws.close()

    async def close(self):
        self._closed = True
        await self._cleanup()
        if self._session and not self._session.closed:
            await self._session.close()

    async def wait_until_ready(self):
        await self._ready.wait()
