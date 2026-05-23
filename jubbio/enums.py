from enum import IntEnum, IntFlag


class ChannelType(IntEnum):
    TEXT = 0
    DM = 1
    VOICE = 2
    CATEGORY = 4


class ButtonStyle(IntEnum):
    PRIMARY = 1
    SECONDARY = 2
    SUCCESS = 3
    DANGER = 4
    LINK = 5


class InteractionType(IntEnum):
    PING = 1
    APPLICATION_COMMAND = 2
    MESSAGE_COMPONENT = 3


class InteractionCallbackType(IntEnum):
    PONG = 1
    CHANNEL_MESSAGE_WITH_SOURCE = 4
    DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE = 5
    DEFERRED_UPDATE_MESSAGE = 6
    UPDATE_MESSAGE = 7


class CommandOptionType(IntEnum):
    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4
    BOOLEAN = 5
    USER = 6
    CHANNEL = 7
    ROLE = 8
    NUMBER = 10


class OverwriteType(IntEnum):
    ROLE = 0
    MEMBER = 1


class Status(IntEnum):
    ONLINE = 1
    IDLE = 2
    DND = 3
    OFFLINE = 4


class Permissions(IntFlag):
    ADMINISTRATOR = 1 << 0
    MANAGE_GUILD = 1 << 1
    MANAGE_CHANNELS = 1 << 2
    MANAGE_ROLES = 1 << 3
    MANAGE_MESSAGES = 1 << 4
    KICK_MEMBERS = 1 << 5
    BAN_MEMBERS = 1 << 6
    SEND_MESSAGES = 1 << 7
    READ_MESSAGES = 1 << 8
    EMBED_LINKS = 1 << 9
    ATTACH_FILES = 1 << 10
    MENTION_EVERYONE = 1 << 11
    USE_EXTERNAL_EMOJIS = 1 << 12
    ADD_REACTIONS = 1 << 13
    CONNECT = 1 << 14
    SPEAK = 1 << 15
    MUTE_MEMBERS = 1 << 16
    DEAFEN_MEMBERS = 1 << 17
    MOVE_MEMBERS = 1 << 18
    MANAGE_NICKNAMES = 1 << 19
    MANAGE_WEBHOOKS = 1 << 20
    CREATE_INVITES = 1 << 21
    VIEW_AUDIT_LOG = 1 << 22
    MANAGE_EMOJIS = 1 << 23
    USE_SLASH_COMMANDS = 1 << 24
    NONE = 0
    ALL = (1 << 25) - 1
