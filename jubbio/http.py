from __future__ import annotations
import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from urllib.parse import quote

import aiohttp

from .errors import JubbioException, HTTPException, Forbidden, NotFound, RateLimited, LoginFailure
from .models import (
    User, BotUser, Member, Guild, Channel, Message, Role,
    Embed, ActionRow, Mentions, MessageReference, Emoji, Attachment,
    Invite, Webhook, PermissionOverwrite,
)

if TYPE_CHECKING:
    from .client import Client

log = logging.getLogger(__name__)

BASE_URL = "https://gateway.jubbio.com/api/v1"


class HTTPClient:

    def __init__(self, token: str, client: "Client" = None):
        self.token = token
        self._client = client
        self._session: Optional[aiohttp.ClientSession] = None
        self._rate_limit_locks: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Event()
        self._global_lock.set()

    @property
    def headers(self) -> dict:
        return {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json",
        }

    async def _ensure_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(headers=self.headers)

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def request(self, method: str, path: str, **kwargs) -> Any:
        await self._ensure_session()
        url = f"{BASE_URL}{path}"

        bucket = f"{method}:{path}"
        if bucket not in self._rate_limit_locks:
            self._rate_limit_locks[bucket] = asyncio.Lock()

        lock = self._rate_limit_locks[bucket]
        last_error = None

        for attempt in range(5):
            await self._global_lock.wait()
            async with lock:
                log.debug(f"{method} {url}")

                async with self._session.request(method, url, **kwargs) as resp:
                    data = None
                    if resp.content_type == "application/json":
                        data = await resp.json()
                    elif resp.status != 204:
                        data = await resp.text()

                    remaining = resp.headers.get("X-RateLimit-Remaining")
                    if remaining == "0":
                        reset_after = float(resp.headers.get("X-RateLimit-Reset-After", "1"))
                        await asyncio.sleep(reset_after)

                    if 200 <= resp.status < 300:
                        return data

                    if resp.status == 429:
                        retry_after = float(resp.headers.get("Retry-After", "1"))
                        log.warning(f"Rate limited! {retry_after}s bekleniyor... ({attempt + 1}/5)")
                        last_error = RateLimited(resp, data)
                        await asyncio.sleep(retry_after)
                        continue

                    if resp.status == 403:
                        raise Forbidden(resp, data)
                    elif resp.status == 404:
                        raise NotFound(resp, data)
                    else:
                        raise HTTPException(resp, data)

        if last_error:
            raise last_error
        raise JubbioException("Maksimum yeniden deneme sayısı aşıldı")

    async def get_me(self) -> BotUser:
        data = await self.request("GET", "/bot/users/@me")
        return BotUser(data)

    async def get_user(self, user_id: str) -> User:
        data = await self.request("GET", f"/bot/users/{user_id}")
        return User(data)


    async def send_message(self, guild_id: str, channel_id: str, content: str = None, *,
                           embed: Embed = None, embeds: List[Embed] = None,
                           components: List[ActionRow] = None, mentions: Mentions = None,
                           reference: MessageReference = None, ephemeral: bool = False) -> Message:
        payload = {}
        if content is not None:
            payload["content"] = content
        if embed:
            payload["embeds"] = [embed.to_dict()]
        elif embeds:
            payload["embeds"] = [e.to_dict() for e in embeds]
        if components:
            payload["components"] = [c.to_dict() for c in components]
        if mentions:
            payload["mentions"] = mentions.to_dict()
        if reference:
            payload["message_reference"] = reference.to_dict()
        if ephemeral:
            payload["ephemeral"] = True

        data = await self.request("POST", f"/bot/guilds/{guild_id}/channels/{channel_id}/messages", json=payload)
        return Message(data, http=self)

    async def edit_message(self, guild_id: str, channel_id: str, message_id: str,
                           content: str = None, *, embed: Embed = None, embeds: List[Embed] = None) -> Message:
        payload = {}
        if content is not None:
            payload["content"] = content
        if embed:
            payload["embeds"] = [embed.to_dict()]
        elif embeds:
            payload["embeds"] = [e.to_dict() for e in embeds]

        data = await self.request("PATCH", f"/bot/guilds/{guild_id}/channels/{channel_id}/messages/{message_id}", json=payload)
        return Message(data, http=self)

    async def delete_message(self, guild_id: str, channel_id: str, message_id: str):
        await self.request("DELETE", f"/bot/guilds/{guild_id}/channels/{channel_id}/messages/{message_id}")

    async def bulk_delete_messages(self, guild_id: str, channel_id: str, message_ids: List[str]):
        await self.request("POST", f"/bot/guilds/{guild_id}/channels/{channel_id}/messages/bulk-delete", json={"messages": message_ids})

    async def get_messages(self, guild_id: str, channel_id: str, limit: int = 50,
                           before: str = None, after: str = None, around: str = None) -> List[Message]:
        params = {"limit": limit}
        if before: params["before"] = before
        if after: params["after"] = after
        if around: params["around"] = around
        data = await self.request("GET", f"/bot/guilds/{guild_id}/channels/{channel_id}/messages", params=params)
        return [Message(m, http=self) for m in (data or [])]

    async def upload_attachment(self, guild_id: str, channel_id: str, file_path: str) -> Attachment:
        filename = os.path.basename(file_path)
        form = aiohttp.FormData()
        with open(file_path, "rb") as f:
            form.add_field("file", f, filename=filename)

            await self._ensure_session()
            url = f"{BASE_URL}/bot/guilds/{guild_id}/channels/{channel_id}/attachments"
            headers = {"Authorization": f"Bot {self.token}"}
            async with self._session.post(url, data=form, headers=headers) as resp:
                if resp.status >= 400:
                    data = await resp.json() if resp.content_type == "application/json" else await resp.text()
                    raise HTTPException(resp, data)
                data = await resp.json()
                return Attachment(data)

    async def send_message_with_files(self, guild_id: str, channel_id: str,
                                      files: List[str], content: str = None, *,
                                      embed: Embed = None, embeds: List[Embed] = None) -> Message:
        payload = {}
        if content is not None:
            payload["content"] = content
        if embed:
            payload["embeds"] = [embed.to_dict()]
        elif embeds:
            payload["embeds"] = [e.to_dict() for e in embeds]

        await self._ensure_session()
        url = f"{BASE_URL}/bot/guilds/{guild_id}/channels/{channel_id}/messages"
        form = aiohttp.FormData()
        form.add_field("payload_json", json.dumps(payload), content_type="application/json")

        file_handles = []
        for i, fp in enumerate(files):
            fh = open(fp, "rb")
            file_handles.append(fh)
            form.add_field(f"files[{i}]", fh, filename=os.path.basename(fp))

        try:
            headers = {"Authorization": f"Bot {self.token}"}
            async with self._session.post(url, data=form, headers=headers) as resp:
                if resp.status >= 400:
                    data = await resp.json() if resp.content_type == "application/json" else await resp.text()
                    raise HTTPException(resp, data)
                data = await resp.json()
                return Message(data, http=self)
        finally:
            for fh in file_handles:
                fh.close()


    async def send_dm(self, user_id: str, content: str = None, *,
                      embed: Embed = None, embeds: List[Embed] = None,
                      components: List[ActionRow] = None, mentions: Mentions = None) -> Message:
        payload = {"recipient_user_id": user_id}
        if content is not None:
            payload["content"] = content
        if embed:
            payload["embeds"] = [embed.to_dict()]
        elif embeds:
            payload["embeds"] = [e.to_dict() for e in embeds]
        if components:
            payload["components"] = [c.to_dict() for c in components]
        if mentions:
            payload["mentions"] = mentions.to_dict()
        data = await self.request("POST", "/bot/dm", json=payload)
        return Message(data, http=self)

    async def send_dm_channel(self, channel_id: str, content: str = None, *, embed: Embed = None) -> Message:
        payload = {}
        if content is not None:
            payload["content"] = content
        if embed:
            payload["embeds"] = [embed.to_dict()]
        data = await self.request("POST", f"/bot/dm/{channel_id}", json=payload)
        return Message(data, http=self)


    async def add_reaction(self, guild_id: str, channel_id: str, message_id: str, emoji: str):
        emoji_encoded = quote(emoji, safe="")
        await self.request("PUT", f"/bot/guilds/{guild_id}/channels/{channel_id}/messages/{message_id}/reactions/{emoji_encoded}/@me")

    async def remove_reaction(self, guild_id: str, channel_id: str, message_id: str, emoji: str):
        emoji_encoded = quote(emoji, safe="")
        await self.request("DELETE", f"/bot/guilds/{guild_id}/channels/{channel_id}/messages/{message_id}/reactions/{emoji_encoded}/@me")

    async def pin_message(self, guild_id: str, channel_id: str, message_id: str):
        await self.request("PUT", f"/bot/guilds/{guild_id}/channels/{channel_id}/pins/{message_id}")

    async def unpin_message(self, guild_id: str, channel_id: str, message_id: str):
        await self.request("DELETE", f"/bot/guilds/{guild_id}/channels/{channel_id}/pins/{message_id}")


    async def create_channel(self, guild_id: str, name: str, type: int = 0, category_id: str = None) -> Channel:
        payload = {"name": name, "type": type}
        if category_id:
            payload["category_id"] = category_id
        data = await self.request("POST", f"/bot/guilds/{guild_id}/channels", json=payload)
        return Channel(data, http=self)

    async def delete_channel(self, guild_id: str, channel_id: str):
        await self.request("DELETE", f"/bot/guilds/{guild_id}/channels/{channel_id}")

    async def delete_category(self, guild_id: str, category_id: str):
        await self.request("DELETE", f"/bot/guilds/{guild_id}/categories/{category_id}")

    async def edit_channel_permissions(self, channel_id: str, overwrite: PermissionOverwrite):
        await self.request("PUT", f"/bot/channels/{channel_id}/permissions/{overwrite.id}", json=overwrite.to_dict())

    async def delete_channel_permissions(self, channel_id: str, overwrite_id: str):
        await self.request("DELETE", f"/bot/channels/{channel_id}/permissions/{overwrite_id}")


    async def get_guild(self, guild_id: str) -> Guild:
        data = await self.request("GET", f"/bot/guilds/{guild_id}")
        return Guild(data, http=self)

    async def get_guild_channels(self, guild_id: str) -> List[Channel]:
        data = await self.request("GET", f"/bot/guilds/{guild_id}/channels")
        channels = []
        for group in (data or []):
            if isinstance(group, dict):
                for ch in group.get("channels", []):
                    channels.append(Channel(ch, http=self))
                cat = group.get("category")
                if cat:
                    channels.append(Channel(cat, http=self))
            elif isinstance(group, list):
                for ch in group:
                    channels.append(Channel(ch, http=self))
        return channels

    async def get_emojis(self, guild_id: str) -> List[Emoji]:
        data = await self.request("GET", f"/bot/guilds/{guild_id}/emojis")
        return [Emoji(e) for e in (data or [])]

    async def get_bans(self, guild_id: str) -> list:
        data = await self.request("GET", f"/bot/guilds/{guild_id}/bans")
        return data or []

    async def get_ban(self, guild_id: str, user_id: str) -> dict:
        return await self.request("GET", f"/bot/guilds/{guild_id}/bans/{user_id}")

    async def get_guild_invites(self, guild_id: str) -> List[Invite]:
        data = await self.request("GET", f"/bot/guilds/{guild_id}/invites")
        return [Invite(i) for i in (data or [])]


    async def get_member(self, guild_id: str, user_id: str) -> Member:
        data = await self.request("GET", f"/bot/guilds/{guild_id}/members/{user_id}")
        return Member(data, guild_id=guild_id, http=self)

    async def get_members(self, guild_id: str, limit: int = 100, cursor: str = None) -> List[Member]:
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        data = await self.request("GET", f"/bot/guilds/{guild_id}/members", params=params)
        return [Member(m, guild_id=guild_id, http=self) for m in (data or [])]

    async def kick_member(self, guild_id: str, user_id: str):
        await self.request("DELETE", f"/bot/guilds/{guild_id}/members/{user_id}")

    async def ban_member(self, guild_id: str, user_id: str, *, reason: str = None, delete_message_days: int = 0):
        payload = {}
        if reason:
            payload["reason"] = reason
        if delete_message_days:
            payload["deleteMessageDays"] = delete_message_days
        await self.request("PUT", f"/bot/guilds/{guild_id}/bans/{user_id}", json=payload)

    async def unban_member(self, guild_id: str, user_id: str):
        await self.request("DELETE", f"/bot/guilds/{guild_id}/bans/{user_id}")

    async def timeout_member(self, guild_id: str, user_id: str, until: str):
        await self.request("POST", f"/bot/guilds/{guild_id}/members/{user_id}/timeout", json={"until": until})

    async def edit_member(self, guild_id: str, user_id: str, *, nick: str = None):
        payload = {}
        if nick is not None:
            payload["nick"] = nick
        await self.request("PATCH", f"/bot/guilds/{guild_id}/members/{user_id}", json=payload)

    async def add_member_role(self, guild_id: str, user_id: str, role_id: str):
        await self.request("PUT", f"/bot/guilds/{guild_id}/members/{user_id}/roles/{role_id}")

    async def remove_member_role(self, guild_id: str, user_id: str, role_id: str):
        await self.request("DELETE", f"/bot/guilds/{guild_id}/members/{user_id}/roles/{role_id}")

    async def bulk_assign_roles(self, guild_id: str, role_ids: List[str], user_ids: List[str]):
        await self.request("PUT", f"/bot/guilds/{guild_id}/members/roles/assign", json={"role_ids": role_ids, "user_ids": user_ids})

    async def bulk_remove_roles(self, guild_id: str, role_ids: List[str], user_ids: List[str]):
        await self.request("DELETE", f"/bot/guilds/{guild_id}/members/roles/remove", json={"role_ids": role_ids, "user_ids": user_ids})


    async def get_roles(self, guild_id: str) -> List[Role]:
        data = await self.request("GET", f"/bot/guilds/{guild_id}/roles")
        return [Role(r) for r in (data or [])]

    async def create_role(self, guild_id: str, **kwargs) -> Role:
        data = await self.request("POST", f"/bot/guilds/{guild_id}/roles", json=kwargs)
        return Role(data)

    async def edit_role(self, guild_id: str, role_id: str, **kwargs) -> Role:
        data = await self.request("PATCH", f"/bot/guilds/{guild_id}/roles/{role_id}", json=kwargs)
        return Role(data)

    async def delete_role(self, guild_id: str, role_id: str):
        await self.request("DELETE", f"/bot/guilds/{guild_id}/roles/{role_id}")


    async def create_invite(self, guild_id: str, channel_id: str, **kwargs) -> Invite:
        data = await self.request("POST", f"/bot/guilds/{guild_id}/channels/{channel_id}/invites", json=kwargs)
        return Invite(data)

    async def get_invite(self, invite_code: str) -> Invite:
        data = await self.request("GET", f"/bot/invites/{invite_code}")
        return Invite(data)

    async def delete_invite(self, invite_code: str):
        await self.request("DELETE", f"/bot/invites/{invite_code}")


    async def create_interaction_response(self, interaction_id: str, token: str,
                                          content: str = None, *, embed: Embed = None,
                                          embeds: List[Embed] = None,
                                          components: List[ActionRow] = None,
                                          ephemeral: bool = False):
        msg_data = {}
        if content is not None:
            msg_data["content"] = content
        if embed:
            msg_data["embeds"] = [embed.to_dict()]
        elif embeds:
            msg_data["embeds"] = [e.to_dict() for e in embeds]
        if components:
            msg_data["components"] = [c.to_dict() for c in components]
        if ephemeral:
            msg_data["flags"] = 64

        await self.request("POST", f"/interactions/{interaction_id}/{token}/callback", json={"type": 4, "data": msg_data})

    async def defer_interaction(self, interaction_id: str, token: str, *, ephemeral: bool = False):
        payload = {"type": 5}
        if ephemeral:
            payload["data"] = {"flags": 64}
        await self.request("POST", f"/interactions/{interaction_id}/{token}/callback", json=payload)

    async def edit_interaction_response(self, app_id: str, token: str,
                                        content: str = None, *, embed: Embed = None, embeds: List[Embed] = None):
        payload = {}
        if content is not None:
            payload["content"] = content
        if embed:
            payload["embeds"] = [embed.to_dict()]
        elif embeds:
            payload["embeds"] = [e.to_dict() for e in embeds]
        await self.request("PATCH", f"/interactions/webhooks/{app_id}/{token}/messages/@original", json=payload)

    async def create_followup(self, app_id: str, token: str, content: str = None, *,
                              embed: Embed = None, embeds: List[Embed] = None, ephemeral: bool = False):
        payload = {}
        if content is not None:
            payload["content"] = content
        if embed:
            payload["embeds"] = [embed.to_dict()]
        elif embeds:
            payload["embeds"] = [e.to_dict() for e in embeds]
        if ephemeral:
            payload["flags"] = 64
        await self.request("POST", f"/interactions/webhooks/{app_id}/{token}", json=payload)


    async def register_global_command(self, app_id: str, command_data: dict):
        return await self.request("POST", f"/applications/{app_id}/commands", json=command_data)

    async def register_guild_command(self, app_id: str, guild_id: str, command_data: dict):
        return await self.request("POST", f"/applications/{app_id}/guilds/{guild_id}/commands", json=command_data)

    async def get_global_commands(self, app_id: str) -> list:
        return await self.request("GET", f"/applications/{app_id}/commands") or []

    async def get_guild_commands(self, app_id: str, guild_id: str) -> list:
        return await self.request("GET", f"/applications/{app_id}/guilds/{guild_id}/commands") or []

    async def get_global_command(self, app_id: str, command_id: str) -> dict:
        return await self.request("GET", f"/applications/{app_id}/commands/{command_id}")

    async def get_guild_command(self, app_id: str, guild_id: str, command_id: str) -> dict:
        return await self.request("GET", f"/applications/{app_id}/guilds/{guild_id}/commands/{command_id}")

    async def update_global_command(self, app_id: str, command_id: str, command_data: dict):
        return await self.request("PATCH", f"/applications/{app_id}/commands/{command_id}", json=command_data)

    async def update_guild_command(self, app_id: str, guild_id: str, command_id: str, command_data: dict):
        return await self.request("PATCH", f"/applications/{app_id}/guilds/{guild_id}/commands/{command_id}", json=command_data)

    async def delete_global_command(self, app_id: str, command_id: str):
        await self.request("DELETE", f"/applications/{app_id}/commands/{command_id}")

    async def delete_guild_command(self, app_id: str, guild_id: str, command_id: str):
        await self.request("DELETE", f"/applications/{app_id}/guilds/{guild_id}/commands/{command_id}")


    async def create_webhook(self, guild_id: str, channel_id: str, name: str) -> Webhook:
        data = await self.request("POST", f"/guilds/{guild_id}/channels/{channel_id}/webhooks", json={"name": name})
        return Webhook(data, http=self)

    async def get_channel_webhooks(self, guild_id: str, channel_id: str) -> List[Webhook]:
        data = await self.request("GET", f"/guilds/{guild_id}/channels/{channel_id}/webhooks")
        return [Webhook(w, http=self) for w in (data or [])]

    async def get_guild_webhooks(self, guild_id: str) -> List[Webhook]:
        data = await self.request("GET", f"/guilds/{guild_id}/webhooks")
        return [Webhook(w, http=self) for w in (data or [])]

    async def get_webhook(self, webhook_id: str, webhook_token: str) -> Webhook:
        data = await self.request("GET", f"/webhooks/{webhook_id}/{webhook_token}")
        return Webhook(data, http=self)

    async def execute_webhook(self, webhook_id: str, webhook_token: str,
                              content: str = None, *, username: str = None,
                              avatar_url: str = None, embeds: List[Embed] = None):
        payload = {}
        if content is not None:
            payload["content"] = content
        if username:
            payload["username"] = username
        if avatar_url:
            payload["avatar_url"] = avatar_url
        if embeds:
            payload["embeds"] = [e.to_dict() for e in embeds]
        await self.request("POST", f"/webhooks/{webhook_id}/{webhook_token}", json=payload)

    async def edit_webhook(self, webhook_id: str, webhook_token: str, *, name: str = None, avatar_url: str = None):
        payload = {}
        if name:
            payload["name"] = name
        if avatar_url:
            payload["avatar_url"] = avatar_url
        await self.request("PATCH", f"/webhooks/{webhook_id}/{webhook_token}", json=payload)

    async def delete_webhook(self, webhook_id: str, webhook_token: str):
        await self.request("DELETE", f"/webhooks/{webhook_id}/{webhook_token}")

    async def execute_webhook_slack(self, webhook_id: str, webhook_token: str, payload: dict):
        await self.request("POST", f"/webhooks/{webhook_id}/{webhook_token}/slack", json=payload)

    async def execute_webhook_github(self, webhook_id: str, webhook_token: str,
                                     payload: dict, event: str, signature: str = None):
        headers = {"X-GitHub-Event": event}
        if signature:
            headers["X-Hub-Signature-256"] = signature
        await self.request("POST", f"/webhooks/{webhook_id}/{webhook_token}/github", json=payload, headers=headers)
