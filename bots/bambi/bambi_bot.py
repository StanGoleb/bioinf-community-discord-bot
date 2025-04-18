import os
import sys
import discord
from discord.ext import commands
from dotenv import load_dotenv
import random
import ruamel.yaml

os.chdir(os.path.dirname(os.path.abspath(__file__)))

project_root_dir = os.path.abspath(os.path.join(os.getcwd(), '..'))
if project_root_dir not in sys.path:
    sys.path.append(project_root_dir)

load_dotenv('tokens.env')
TOKEN = os.getenv('DISCORD_TOKEN')
BOT_PREFIX = os.getenv('BOT_PREFIX', '@')
BOT_NAME = os.getenv('BOT_NAME', 'Bambi')
BOT_PERM = int(os.getenv('BOT_PERM', '0'))

intents = discord.Intents.default()
intents.message_content = True

activity = discord.Activity(type=discord.ActivityType.listening, name="BFF - bambi, Young Leosia, PG$, @atutowy")

yaml = ruamel.yaml.YAML()

class BambiBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=BOT_PREFIX, intents=intents, activity=activity)
        self.bot_name = BOT_NAME
        self.bot_prefix = BOT_PREFIX
        self.dis_token = TOKEN
        self.bot_perm = BOT_PERM
        self.cog = None

    async def setup_hook(self):
        await self.load_extension("main_cogs")
        self.cog = self.get_cog("MainCommands")

        @self.command(help="Wylosuj losowy wers piosenki")
        async def wers(ctx):
            with open("wers.yaml", encoding="utf-8") as wfile:
                data = yaml.load(wfile)
            with open("przywitania.yaml", encoding="utf-8") as pfile:
                greetings = yaml.load(pfile)
            random_song = random.choice(list(data.keys()))
            random_line = random.choice(data[random_song])
            random_greeting = random.choice(greetings)
            await ctx.send(f"{random_greeting}\n{random_line}\n{random_song}")

bot = BambiBot()
bot.run(TOKEN)
