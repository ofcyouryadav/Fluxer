import discord, os
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb+srv://fluxer8585:fluxer8585@fluxer.3izoeeq.mongodb.net/?appName=Fluxer"
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["FluxerBotV2"]

# Spotify Configuration
SPOTIFY_CLIENT_ID = "66d272bbbea144f1b01d632f257c43db"
SPOTIFY_CLIENT_SECRET = "353bf3974c024718939f7301a31b03c5"


def owner():

    async def predicate(ctx: commands.Context):
        data = await db.owner.find_one({"owners": ctx.bot.user.id})
        if data is None:
            return
        ids = data["user_id"]
        if ctx.author.id in ids:
            return True
        else:
            return False

    return commands.check(predicate)


## OWNER IDS
OWNER_IDS = [458651863668228096,327878682314014721 ]

def bot_owner():

    async def predicate(ctx: commands.Context):
        if ctx.author.id in OWNER_IDS:
            return True
        else:
            return False

    return commands.check(predicate)


## COLORS
default = "0x2f3136"
red = "0xff0000"
green = "0x00ff00"
yellow = "0xffff00"

## EMOJIS
check = "<:Zycron_Enabled:1415892977749987359>"
cross = "<:Zycron_Disabled:1415893171690537101>"
home = "<:ayami_Home:1442615227211452577>"
all = "<:xieron_supoortscommandsbadge:1442614853742366741>"
music = "<a:Arziyaan_Music:1438464271729168407>"
filters = "<:filters:1312319460954345553>"
spotify = "<a:spotify:1442614063459995778>"
playlist = "<:playlists:1442614310378537121>"
settings = "<a:settings:1311610012472311821>"

## MAIN URLS
## vote = "https://top.gg"
invite = "https://discord.com/oauth2/authorize?client_id=914785889329233931"
support_server = "https://discord.gg/jw6n7g5zbZ"  # Added support_server URL
support = "https://discord.gg/jw6n7g5zbZ"

## LOGS WEBHOOK URLS ##
join_log = "https://discord.com/api/webhooks/1435492729634291773/j2WxrNB02jidWK1vFgDjn6VfzYmChW3WYxdVPm9GBwNfe1ZX7PU6b2qkKLqOoUHq6v5e"
leave_log = "https://discord.com/api/webhooks/1435492729634291773/j2WxrNB02jidWK1vFgDjn6VfzYmChW3WYxdVPm9GBwNfe1ZX7PU6b2qkKLqOoUHq6v5e"
player_create = "https://discord.com/api/webhooks/1435492729634291773/j2WxrNB02jidWK1vFgDjn6VfzYmChW3WYxdVPm9GBwNfe1ZX7PU6b2qkKLqOoUHq6v5e"
player_delete = "https://discord.com/api/webhooks/1435492729634291773/j2WxrNB02jidWK1vFgDjn6VfzYmChW3WYxdVPm9GBwNfe1ZX7PU6b2qkKLqOoUHq6v5e"
stuck = "https://discord.com/api/webhooks/1435492729634291773/j2WxrNB02jidWK1vFgDjn6VfzYmChW3WYxdVPm9GBwNfe1ZX7PU6b2qkKLqOoUHq6v5e"
exceptt = "https://discord.com/api/webhooks/1435492729634291773/j2WxrNB02jidWK1vFgDjn6VfzYmChW3WYxdVPm9GBwNfe1ZX7PU6b2qkKLqOoUHq6v5e"
command_log = "https://discord.com/api/webhooks/1435492729634291773/j2WxrNB02jidWK1vFgDjn6VfzYmChW3WYxdVPm9GBwNfe1ZX7PU6b2qkKLqOoUHq6v5e"
## BOT URLS ##
bot_icon = "https://cdn.discordapp.com/avatars/914785889329233931/acc9c19e09a7896237899937b57d9d89.png?size=1024"

invite = "https://discord.com/oauth2/authorize?client_id=914785889329233931"
link = "https://discord.gg/jw6n7g5zbZ"
