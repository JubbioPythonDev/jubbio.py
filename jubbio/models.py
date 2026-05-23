from __future__ import annotations
from typing import List, Optional
from .enums import ChannelType, ButtonStyle, CommandOptionType, OverwriteType


class Color:
    def __init__(self, value: int = 0):
        self.value = value

    @classmethod
    def red(cls): return cls(0xFF0000)
    @classmethod
    def green(cls): return cls(0x00FF00)
    @classmethod
    def blue(cls): return cls(0x0000FF)
    @classmethod
    def gold(cls): return cls(0xFFD700)
    @classmethod
    def purple(cls): return cls(0x9B59B6)
    @classmethod
    def orange(cls): return cls(0xE67E22)
    @classmethod
    def white(cls): return cls(0xFFFFFF)
    @classmethod
    def dark(cls): return cls(0x2C2F33)
    @classmethod
    def from_rgb(cls, r, g, b): return cls((r << 16) + (g << 8) + b)


class Intents:
    GUILDS = 1 << 0
    GUILD_MEMBERS = 1 << 1
    GUILD_MODERATION = 1 << 2
    GUILD_EMOJIS_AND_STICKERS = 1 << 3
    GUILD_INTEGRATIONS = 1 << 4
    GUILD_WEBHOOKS = 1 << 5
    GUILD_INVITES = 1 << 6
    GUILD_VOICE_STATES = 1 << 7
    GUILD_PRESENCES = 1 << 8
    GUILD_MESSAGES = 1 << 9
    GUILD_MESSAGE_REACTIONS = 1 << 10
    GUILD_MESSAGE_TYPING = 1 << 11
    DIRECT_MESSAGES = 1 << 12
    DIRECT_MESSAGE_REACTIONS = 1 << 13
    DIRECT_MESSAGE_TYPING = 1 << 14
    MESSAGE_CONTENT = 1 << 15
    GUILD_SCHEDULED_EVENTS = 1 << 16
    AUTO_MODERATION_CONFIGURATION = 1 << 20
    AUTO_MODERATION_EXECUTION = 1 << 21

    def __init__(self, value: int = 0):
        self.value = value

    @classmethod
    def all(cls):
        return cls(
            cls.GUILDS | cls.GUILD_MEMBERS | cls.GUILD_MODERATION |
            cls.GUILD_EMOJIS_AND_STICKERS | cls.GUILD_INTEGRATIONS |
            cls.GUILD_WEBHOOKS | cls.GUILD_INVITES | cls.GUILD_VOICE_STATES |
            cls.GUILD_PRESENCES | cls.GUILD_MESSAGES | cls.GUILD_MESSAGE_REACTIONS |
            cls.GUILD_MESSAGE_TYPING | cls.DIRECT_MESSAGES |
            cls.DIRECT_MESSAGE_REACTIONS | cls.DIRECT_MESSAGE_TYPING |
            cls.MESSAGE_CONTENT | cls.GUILD_SCHEDULED_EVENTS |
            cls.AUTO_MODERATION_CONFIGURATION | cls.AUTO_MODERATION_EXECUTION
        )

    @classmethod
    def default(cls):
        return cls(cls.GUILDS | cls.GUILD_MESSAGES | cls.DIRECT_MESSAGES | cls.MESSAGE_CONTENT)

    @classmethod
    def none(cls):
        return cls(0)


class User:
    __slots__ = ("id", "username", "display_name", "avatar_url", "bot", "_data")

    def __init__(self, data: dict):
        self._data = data
        self.id: str = data.get("id", "")
        self.username: str = data.get("username", "")
        self.display_name: str = data.get("display_name", self.username)
        self.avatar_url: Optional[str] = data.get("avatar_url")
        self.bot: bool = data.get("bot", False)

    def __str__(self):
        return self.display_name or self.username

    def __repr__(self):
        return f"<User id={self.id} username='{self.username}'>"

    @property
    def mention(self):
        return f"<@{self.id}>"


class BotUser(User):
    __slots__ = ("application_id",)

    def __init__(self, data: dict):
        super().__init__(data)
        self.application_id: str = data.get("application_id", self.id)
        self.bot = True


class EmbedField:
    def __init__(self, name: str, value: str, inline: bool = False):
        self.name = name
        self.value = value
        self.inline = inline

    def to_dict(self):
        return {"name": self.name, "value": self.value, "inline": self.inline}


class EmbedAuthor:
    def __init__(self, name: str, url: str = None, icon_url: str = None):
        self.name = name
        self.url = url
        self.icon_url = icon_url

    def to_dict(self):
        d = {"name": self.name}
        if self.url: d["url"] = self.url
        if self.icon_url: d["icon_url"] = self.icon_url
        return d


class EmbedFooter:
    def __init__(self, text: str, icon_url: str = None):
        self.text = text
        self.icon_url = icon_url

    def to_dict(self):
        d = {"text": self.text}
        if self.icon_url: d["icon_url"] = self.icon_url
        return d


class EmbedImage:
    def __init__(self, url: str):
        self.url = url

    def to_dict(self):
        return {"url": self.url}


class EmbedThumbnail:
    def __init__(self, url: str):
        self.url = url

    def to_dict(self):
        return {"url": self.url}


class Embed:
    def __init__(self, *, title: str = None, description: str = None,
                 color: int | Color = None, url: str = None, timestamp: str = None):
        self.title = title
        self.description = description
        self.color = color.value if isinstance(color, Color) else color
        self.url = url
        self.timestamp = timestamp
        self.fields: List[EmbedField] = []
        self.author: Optional[EmbedAuthor] = None
        self.footer: Optional[EmbedFooter] = None
        self.image: Optional[EmbedImage] = None
        self.thumbnail: Optional[EmbedThumbnail] = None

    def add_field(self, name: str, value: str, inline: bool = False):
        self.fields.append(EmbedField(name, value, inline))
        return self

    def set_author(self, name: str, url: str = None, icon_url: str = None):
        self.author = EmbedAuthor(name, url, icon_url)
        return self

    def set_footer(self, text: str, icon_url: str = None):
        self.footer = EmbedFooter(text, icon_url)
        return self

    def set_image(self, url: str):
        self.image = EmbedImage(url)
        return self

    def set_thumbnail(self, url: str):
        self.thumbnail = EmbedThumbnail(url)
        return self

    def to_dict(self):
        d = {}
        if self.title: d["title"] = self.title
        if self.description: d["description"] = self.description
        if self.color is not None: d["color"] = self.color
        if self.url: d["url"] = self.url
        if self.timestamp: d["timestamp"] = self.timestamp
        if self.fields: d["fields"] = [f.to_dict() for f in self.fields]
        if self.author: d["author"] = self.author.to_dict()
        if self.footer: d["footer"] = self.footer.to_dict()
        if self.image: d["image"] = self.image.to_dict()
        if self.thumbnail: d["thumbnail"] = self.thumbnail.to_dict()
        return d


class Button:
    def __init__(self, *, style: int = ButtonStyle.PRIMARY, label: str = None,
                 custom_id: str = None, url: str = None, disabled: bool = False, emoji: str = None):
        self.type = 2
        self.style = style
        self.label = label
        self.custom_id = custom_id
        self.url = url
        self.disabled = disabled
        self.emoji = emoji

    def to_dict(self):
        d = {"type": self.type, "style": self.style}
        if self.label: d["label"] = self.label
        if self.custom_id: d["custom_id"] = self.custom_id
        if self.url: d["url"] = self.url
        if self.disabled: d["disabled"] = self.disabled
        if self.emoji: d["emoji"] = self.emoji
        return d


class SelectOption:
    def __init__(self, label: str, value: str, description: str = None, default: bool = False):
        self.label = label
        self.value = value
        self.description = description
        self.default = default

    def to_dict(self):
        d = {"label": self.label, "value": self.value}
        if self.description: d["description"] = self.description
        if self.default: d["default"] = self.default
        return d


class SelectMenu:
    def __init__(self, *, custom_id: str, options: List[SelectOption] = None,
                 placeholder: str = None, min_values: int = 1, max_values: int = 1):
        self.type = 3
        self.custom_id = custom_id
        self.options = options or []
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values

    def to_dict(self):
        d = {"type": self.type, "custom_id": self.custom_id,
             "options": [o.to_dict() for o in self.options],
             "min_values": self.min_values, "max_values": self.max_values}
        if self.placeholder: d["placeholder"] = self.placeholder
        return d


class ActionRow:
    def __init__(self, *components):
        self.type = 1
        self.components = list(components)

    def to_dict(self):
        return {"type": self.type, "components": [c.to_dict() for c in self.components]}


class Mentions:
    def __init__(self, *, users: List[str] = None, roles: List[str] = None, everyone: bool = False):
        self.users = users or []
        self.roles = roles or []
        self.everyone = everyone

    def to_dict(self):
        return {"users": self.users, "roles": self.roles, "everyone": self.everyone}


class MessageReference:
    def __init__(self, message_id: str):
        self.message_id = message_id

    def to_dict(self):
        return {"message_id": self.message_id}


class PermissionOverwrite:
    def __init__(self, id: str, type: int = OverwriteType.ROLE, allow: int = 0, deny: int = 0):
        self.id = id
        self.type = type
        self.allow = allow
        self.deny = deny

    def to_dict(self):
        return {"id": self.id, "type": self.type, "allow": self.allow, "deny": self.deny}


class Emoji:
    def __init__(self, data: dict):
        self.id: str = data.get("id", "")
        self.name: str = data.get("name", "")
        self.animated: bool = data.get("animated", False)
        self.url: Optional[str] = data.get("url")

    def __str__(self):
        if self.id:
            prefix = "a" if self.animated else ""
            return f"<{prefix}:{self.name}:{self.id}>"
        return f":{self.name}:"


class Attachment:
    def __init__(self, data: dict):
        self.id: str = data.get("ID", data.get("id", ""))
        self.message_id: str = data.get("MessageID", data.get("message_id", ""))
        self.filename: str = data.get("Filename", data.get("filename", ""))
        self.content_type: str = data.get("ContentType", data.get("content_type", ""))
        self.size: int = data.get("Size", data.get("size", 0))
        self.url: str = data.get("URL", data.get("url", ""))


class Role:
    def __init__(self, data: dict):
        self.id: str = data.get("id", "")
        self.name: str = data.get("name", "")
        self.color: int = data.get("color", 0)
        self.position: int = data.get("position", 0)
        self.permissions: int = data.get("permissions", 0)
        self.hoist: bool = data.get("hoist", False)
        self.mentionable: bool = data.get("mentionable", False)

    def __str__(self):
        return self.name

    @property
    def mention(self):
        return f"<@&{self.id}>"


class Channel:
    def __init__(self, data: dict, http=None):
        self._http = http
        self._data = data
        self.id: str = data.get("id", "")
        self.name: str = data.get("name", "")
        self.type: int = data.get("type", 0)
        self.guild_id: str = data.get("guild_id", "")
        self.position: int = data.get("position", 0)
        self.category_id: Optional[str] = data.get("category_id")
        self.topic: Optional[str] = data.get("topic")

    def __str__(self):
        return self.name

    @property
    def mention(self):
        return f"<#{self.id}>"

    async def send(self, content: str = None, *, embed: Embed = None, embeds: List[Embed] = None,
                   components: List[ActionRow] = None, mentions: Mentions = None,
                   reference: MessageReference = None, ephemeral: bool = False):
        return await self._http.send_message(
            self.guild_id, self.id, content=content, embed=embed, embeds=embeds,
            components=components, mentions=mentions, reference=reference, ephemeral=ephemeral
        )

    async def fetch_messages(self, limit: int = 50, before: str = None, after: str = None):
        return await self._http.get_messages(self.guild_id, self.id, limit=limit, before=before, after=after)

    async def purge(self, message_ids: List[str]):
        return await self._http.bulk_delete_messages(self.guild_id, self.id, message_ids)

    async def delete(self):
        return await self._http.delete_channel(self.guild_id, self.id)

    async def set_permissions(self, overwrite: PermissionOverwrite):
        return await self._http.edit_channel_permissions(self.id, overwrite)


class Member:
    def __init__(self, data: dict, guild_id: str = None, http=None):
        self._http = http
        self._data = data
        self.guild_id = guild_id or data.get("guild_id", "")
        user_data = data.get("user", data)
        self.user = User(user_data) if isinstance(user_data, dict) else user_data
        self.id: str = self.user.id if isinstance(self.user, User) else data.get("id", "")
        self.nick: Optional[str] = data.get("nick") or data.get("nickname")
        self.roles: List[str] = data.get("roles", [])
        self.joined_at: Optional[str] = data.get("joined_at")

    def __str__(self):
        return self.nick or str(self.user)

    @property
    def display_name(self):
        return self.nick or self.user.display_name

    @property
    def mention(self):
        return f"<@{self.id}>"

    async def add_role(self, role_id: str):
        return await self._http.add_member_role(self.guild_id, self.id, role_id)

    async def remove_role(self, role_id: str):
        return await self._http.remove_member_role(self.guild_id, self.id, role_id)

    async def kick(self):
        return await self._http.kick_member(self.guild_id, self.id)

    async def ban(self, *, reason: str = None, delete_message_days: int = 0):
        return await self._http.ban_member(self.guild_id, self.id, reason=reason,
                                           delete_message_days=delete_message_days)

    async def timeout(self, until: str):
        return await self._http.timeout_member(self.guild_id, self.id, until)

    async def edit(self, *, nick: str = None):
        return await self._http.edit_member(self.guild_id, self.id, nick=nick)


class Guild:
    def __init__(self, data: dict, http=None):
        self._http = http
        self._data = data
        self.id: str = data.get("id", "")
        self.name: str = data.get("name", "")
        self.icon_url: Optional[str] = data.get("icon_url")
        self.owner_id: Optional[str] = data.get("owner_id")
        self.member_count: int = data.get("member_count", 0)

    def __str__(self):
        return self.name

    async def fetch_channels(self):
        return await self._http.get_guild_channels(self.id)

    async def create_channel(self, name: str, type: int = ChannelType.TEXT, category_id: str = None):
        return await self._http.create_channel(self.id, name, type, category_id)

    async def fetch_member(self, user_id: str):
        return await self._http.get_member(self.id, user_id)

    async def fetch_members(self, limit: int = 100, cursor: str = None):
        return await self._http.get_members(self.id, limit=limit, cursor=cursor)

    async def fetch_roles(self):
        return await self._http.get_roles(self.id)

    async def create_role(self, **kwargs):
        return await self._http.create_role(self.id, **kwargs)

    async def fetch_emojis(self):
        return await self._http.get_emojis(self.id)

    async def fetch_bans(self):
        return await self._http.get_bans(self.id)

    async def unban(self, user_id: str):
        return await self._http.unban_member(self.id, user_id)


class Message:
    def __init__(self, data: dict, http=None):
        self._http = http
        self._data = data
        self.id: str = data.get("id", "")
        self.content: str = data.get("content", "")
        self.channel_id: str = data.get("channel_id", "")
        self.guild_id: str = data.get("guild_id", "")
        author_data = data.get("author", {})
        self.author = User(author_data) if isinstance(author_data, dict) else author_data
        self.embeds: list = data.get("embeds", [])
        self.attachments = [Attachment(a) for a in data.get("attachments", [])]
        self.timestamp: Optional[str] = data.get("timestamp")
        self.edited_timestamp: Optional[str] = data.get("edited_timestamp")
        self.pinned: bool = data.get("pinned", False)
        self.mention_everyone: bool = data.get("mention_everyone", False)
        self.mentions: list = data.get("mentions", [])
        self._channel: Optional[Channel] = None

    @property
    def channel(self):
        if self._channel is None and self._http:
            self._channel = Channel({"id": self.channel_id, "guild_id": self.guild_id}, http=self._http)
        return self._channel

    async def reply(self, content: str = None, **kwargs):
        kwargs["reference"] = MessageReference(self.id)
        return await self._http.send_message(self.guild_id, self.channel_id, content=content, **kwargs)

    async def edit(self, content: str = None, *, embed: Embed = None, embeds: List[Embed] = None):
        return await self._http.edit_message(self.guild_id, self.channel_id, self.id,
                                             content=content, embed=embed, embeds=embeds)

    async def delete(self):
        return await self._http.delete_message(self.guild_id, self.channel_id, self.id)

    async def add_reaction(self, emoji: str):
        return await self._http.add_reaction(self.guild_id, self.channel_id, self.id, emoji)

    async def remove_reaction(self, emoji: str):
        return await self._http.remove_reaction(self.guild_id, self.channel_id, self.id, emoji)

    async def pin(self):
        return await self._http.pin_message(self.guild_id, self.channel_id, self.id)

    async def unpin(self):
        return await self._http.unpin_message(self.guild_id, self.channel_id, self.id)


class Invite:
    def __init__(self, data: dict):
        self.code: str = data.get("code", "")
        self.guild: Optional[dict] = data.get("guild")
        self.channel: Optional[dict] = data.get("channel")
        self.inviter: Optional[dict] = data.get("inviter")
        self.uses: int = data.get("uses", 0)
        self.max_uses: int = data.get("max_uses", 0)
        self.expires_at: Optional[str] = data.get("expires_at")

    @property
    def url(self):
        return f"https://jubbio.com/invite/{self.code}"


class Webhook:
    def __init__(self, data: dict, http=None):
        self._http = http
        self.id: str = data.get("id", "")
        self.name: str = data.get("name", "")
        self.token: str = data.get("token", "")
        self.channel_id: str = data.get("channel_id", "")
        self.guild_id: str = data.get("guild_id", "")
        self.avatar_url: Optional[str] = data.get("avatar_url")

    @property
    def url(self):
        return f"https://gateway.jubbio.com/api/v1/webhooks/{self.id}/{self.token}"

    async def send(self, content: str = None, *, username: str = None, avatar_url: str = None,
                   embeds: List[Embed] = None):
        return await self._http.execute_webhook(self.id, self.token, content=content,
                                                username=username, avatar_url=avatar_url, embeds=embeds)

    async def edit(self, *, name: str = None, avatar_url: str = None):
        return await self._http.edit_webhook(self.id, self.token, name=name, avatar_url=avatar_url)

    async def delete(self):
        return await self._http.delete_webhook(self.id, self.token)


class Interaction:
    def __init__(self, data: dict, http=None):
        self._http = http
        self._data = data
        self.id: str = data.get("id", "")
        self.type: int = data.get("type", 0)
        self.token: str = data.get("token", "")
        self.guild_id: str = data.get("guild_id", "")
        self.channel_id: str = data.get("channel_id", "")
        self.application_id: str = data.get("application_id", "")
        idata = data.get("data", {})
        self.command_name: str = idata.get("name", "")
        self.command_id: str = idata.get("id", "")
        self.custom_id: str = idata.get("custom_id", "")
        self.options: list = idata.get("options", [])
        self.values: list = idata.get("values", [])
        member_data = data.get("member", {})
        self.member = Member(member_data, guild_id=self.guild_id) if member_data else None
        self.user = self.member.user if self.member else User(data.get("user", {}))
        self._responded = False

    def get_option(self, name: str, default=None):
        for opt in self.options:
            if opt.get("name") == name:
                return opt.get("value", default)
        return default

    async def respond(self, content: str = None, *, embed: Embed = None, embeds: List[Embed] = None,
                      components: List[ActionRow] = None, ephemeral: bool = False):
        self._responded = True
        return await self._http.create_interaction_response(
            self.id, self.token, content=content, embed=embed, embeds=embeds,
            components=components, ephemeral=ephemeral
        )

    async def defer(self, *, ephemeral: bool = False):
        self._responded = True
        return await self._http.defer_interaction(self.id, self.token, ephemeral=ephemeral)

    async def edit_original(self, content: str = None, *, embed: Embed = None, embeds: List[Embed] = None):
        return await self._http.edit_interaction_response(
            self.application_id, self.token, content=content, embed=embed, embeds=embeds
        )

    async def followup(self, content: str = None, *, embed: Embed = None, embeds: List[Embed] = None,
                       ephemeral: bool = False):
        return await self._http.create_followup(
            self.application_id, self.token, content=content, embed=embed, embeds=embeds, ephemeral=ephemeral
        )


InteractionResponse = Interaction


class SlashCommandOption:
    def __init__(self, name: str, description: str, type: int = CommandOptionType.STRING,
                 required: bool = False, choices: list = None):
        self.name = name
        self.description = description
        self.type = type
        self.required = required
        self.choices = choices

    def to_dict(self):
        d = {"name": self.name, "description": self.description, "type": self.type, "required": self.required}
        if self.choices: d["choices"] = self.choices
        return d


class SlashCommand:
    def __init__(self, name: str, description: str, options: List[SlashCommandOption] = None):
        self.name = name
        self.description = description
        self.options = options or []

    def to_dict(self):
        d = {"name": self.name, "description": self.description}
        if self.options: d["options"] = [o.to_dict() for o in self.options]
        return d
