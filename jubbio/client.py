from __future__ import annotations
import asyncio
import logging
from typing import Callable, Dict, List, Optional

from .http import HTTPClient
from .gateway import Gateway
from .models import (
    User, BotUser, Member, Guild, Channel, Message, Role,
    Embed, ActionRow, Mentions, MessageReference, Emoji,
    Invite, Webhook, Interaction, SlashCommand, Intents,
)
from .errors import LoginFailure

log = logging.getLogger(__name__)


class Client:

    def __init__(self, intents: Intents = None):
        self.intents = intents or Intents.default()
        self._http: Optional[HTTPClient] = None
        self._gateway: Optional[Gateway] = None
        self._token: Optional[str] = None
        self._closed = False
        self._ready = asyncio.Event()
        self._event_handlers: Dict[str, Callable] = {}
        self._command_handlers: Dict[str, Callable] = {}
        self._component_handlers: Dict[str, Callable] = {}
        self.user: Optional[BotUser] = None
        self.application_id: Optional[str] = None
        self.guilds: List[Guild] = []

    def event(self, func: Callable) -> Callable:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Olay dinleyicisi async olmalıdır")
        self._event_handlers[func.__name__] = func
        return func

    def command(self, name: str = None):
        def decorator(func: Callable) -> Callable:
            if not asyncio.iscoroutinefunction(func):
                raise TypeError("Komut dinleyicisi async olmalıdır")
            self._command_handlers[name or func.__name__] = func
            return func
        return decorator

    def component(self, custom_id: str):
        def decorator(func: Callable) -> Callable:
            if not asyncio.iscoroutinefunction(func):
                raise TypeError("Bileşen dinleyicisi async olmalıdır")
            self._component_handlers[custom_id] = func
            return func
        return decorator

    def on(self, event_name: str):
        def decorator(func: Callable) -> Callable:
            if not asyncio.iscoroutinefunction(func):
                raise TypeError("Olay dinleyicisi async olmalıdır")
            full_name = f"on_{event_name}" if not event_name.startswith("on_") else event_name
            self._event_handlers[full_name] = func
            return func
        return decorator

    async def _handle_ready(self, data: dict):
        user_data = data.get("user", data.get("bot", {}))
        self.user = BotUser(user_data)
        self.application_id = self.user.application_id
        self.guilds = [Guild(g, http=self._http) for g in data.get("guilds", [])]
        self._ready.set()

        if "on_ready" in self._event_handlers:
            await self._event_handlers["on_ready"]()

    async def _dispatch(self, event_name: str, data: dict):
        try:
            if event_name == "on_message":
                message = Message(data, http=self._http)
                if message.author.id == (self.user.id if self.user else None):
                    return
                if event_name in self._event_handlers:
                    await self._event_handlers[event_name](message)

            elif event_name == "on_interaction":
                interaction = Interaction(data, http=self._http)
                if interaction.type == 2 and interaction.command_name in self._command_handlers:
                    await self._command_handlers[interaction.command_name](interaction)
                elif interaction.type == 3 and interaction.custom_id in self._component_handlers:
                    await self._component_handlers[interaction.custom_id](interaction)
                elif event_name in self._event_handlers:
                    await self._event_handlers[event_name](interaction)

            elif event_name in ("on_guild_join", "on_guild_remove"):
                guild = Guild(data, http=self._http)
                if event_name in self._event_handlers:
                    await self._event_handlers[event_name](guild)

            elif event_name in ("on_member_ban", "on_member_unban", "on_member_join", "on_member_remove"):
                member = Member(data, guild_id=data.get("guild_id", ""), http=self._http)
                if event_name in self._event_handlers:
                    await self._event_handlers[event_name](member)

            elif event_name in ("on_invite_create", "on_invite_delete"):
                if event_name in self._event_handlers:
                    await self._event_handlers[event_name](Invite(data))

            else:
                if event_name in self._event_handlers:
                    await self._event_handlers[event_name](data)

        except Exception as e:
            log.error("Olay hatası (%s): %s", event_name, e, exc_info=True)
            if "on_error" in self._event_handlers:
                await self._event_handlers["on_error"](event_name, e)

    async def start(self, token: str):
        self._token = token
        self._http = HTTPClient(token, client=self)
        self._gateway = Gateway(self, token)

        try:
            self.user = await self._http.get_me()
            self.application_id = self.user.application_id
        except Exception as e:
            raise LoginFailure(f"Giriş başarısız: {e}") from e

        await self._gateway.connect()

        try:
            while not self._closed:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    def run(self, token: str):
        async def runner():
            try:
                await self.start(token)
            except KeyboardInterrupt:
                pass
            finally:
                await self.close()

        try:
            asyncio.run(runner())
        except KeyboardInterrupt:
            pass

    async def close(self):
        self._closed = True
        if self._gateway:
            await self._gateway.close()
        if self._http:
            await self._http.close()

    async def wait_until_ready(self):
        await self._ready.wait()

    async def get_user(self, user_id: str) -> User:
        return await self._http.get_user(user_id)

    async def get_guild(self, guild_id: str) -> Guild:
        return await self._http.get_guild(guild_id)

    async def send_dm(self, user_id: str, content: str = None, **kwargs) -> Message:
        return await self._http.send_dm(user_id, content, **kwargs)

    async def get_invite(self, code: str) -> Invite:
        return await self._http.get_invite(code)

    async def register_command(self, command: SlashCommand, guild_id: str = None):
        if not self.application_id:
            raise RuntimeError("Bot henüz hazır değil")
        if guild_id:
            return await self._http.register_guild_command(self.application_id, guild_id, command.to_dict())
        return await self._http.register_global_command(self.application_id, command.to_dict())

    async def delete_command(self, command_id: str, guild_id: str = None):
        if not self.application_id:
            raise RuntimeError("Bot henüz hazır değil")
        if guild_id:
            await self._http.delete_guild_command(self.application_id, guild_id, command_id)
        else:
            await self._http.delete_global_command(self.application_id, command_id)

    async def get_commands(self, guild_id: str = None) -> list:
        if not self.application_id:
            raise RuntimeError("Bot henüz hazır değil")
        if guild_id:
            return await self._http.get_guild_commands(self.application_id, guild_id)
        return await self._http.get_global_commands(self.application_id)
