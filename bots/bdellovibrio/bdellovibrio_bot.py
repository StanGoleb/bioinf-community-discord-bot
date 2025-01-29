import os
import sys
import discord
from discord.ext import commands
from dotenv import load_dotenv
import ruamel.yaml

from datetime import date, timedelta
import re
import random

os.chdir(os.path.dirname(os.path.abspath(__file__)))
project_root_dir = os.path.abspath(os.path.join(os.getcwd(), '..', '..'))
if project_root_dir not in sys.path:
    sys.path.append(project_root_dir)

load_dotenv(os.path.join('tokens.env'))
TOKEN = os.getenv('DISCORD_TOKEN')
BOT_PREFIX = os.getenv('BOT_PREFIX')
BOT_NAME = os.getenv('BOT_NAME')
BOT_PERM = int(os.getenv('BOT_PERM'))
WITAJ_MSG_ID = int(os.getenv('WITAJ_MSG_ID'))
WITAJ_GUILD_ID = int(os.getenv('WITAJ_GUILD_ID'))
YEARLY_CHANNELS_CATEGORY_ID = int(os.getenv('YEARLY_CHANNELS_CATEGORY_ID'))

intents = discord.Intents.default()
intents.message_content = True

activity = discord.Activity(type=discord.ActivityType.watching, name="Imago Biologia 🦋")

class BdellovibrioBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=BOT_PREFIX, intents=intents, activity=activity)
        self.bot_name = BOT_NAME
        self.bot_prefix = BOT_PREFIX
        self.dis_token = TOKEN
        self.bot_perm = BOT_PERM
        self.cog = None


    async def on_ready(self):
        await self.load_extension("bots.main_cogs")
        self.cog = self.get_cog('MainCommands')
        
        print(f'Logged in as {self.user}')

    async def reformat_date(self, ctx, day_info):

        timedelta_pattern = r"^[-+]?\d+$"
        dd_mm_pattern = r'^\d{1,2}\.\d{1,2}$'
        dd_mm_yy_pattern = r'^\d{1,2}\.\d{1,2}\.\d{2}$'
        dd_mm_yyyy_pattern = r'^\d{1,2}\.\d{1,2}\.\d{4}$'


        today = date.today()
        final_date = None

        if re.match(dd_mm_yyyy_pattern, day_info):
            day, month, year = day_info.split(".")
            year = year[2:]
            day = f"{int(day):02}"
            month = f"{int(month):02}"
            final_date = f"{day}.{month}.{year}"

        elif re.match(dd_mm_yy_pattern, day_info):
            day, month, year = day_info.split(".")
            day = f"{int(day):02}"
            month = f"{int(month):02}"
            final_date = f"{day}.{month}.{year}"

        elif re.match(dd_mm_pattern, day_info):
            day, month = day_info.split(".")
            day = f"{int(day):02}"
            month = f"{int(month):02}"
            year = str(today.year)[2:]
            
            if int(month) > int(today.month):
                year = str(int(year) - 1)
            elif int(month) == int(today.month) and int(day) > int(today.day):
                year = str(int(year) - 1)
            
            final_date = f"{day}.{month}.{year}"

        elif re.match(timedelta_pattern, day_info):
            delta = int(day_info)
            final_date = (today + timedelta(days=delta)).strftime("%d.%m.%y")

        else:
            await ctx.invoke(self.get_command("help"), command_to_help="slowo")
            return None
        return final_date

    async def setup_hook(self):

        @self.command(help="Wanda zmieniła sposób wywoływania komend. Od teraz, zwracaj się do Wandy przy użyciu '%komenda'")
        async def plyny(ctx):
            await ctx.send("Wanda zmieniła sposób wywoływania komend. Od teraz, zwracaj się do Wandy przy użyciu '%komenda'")

        @self.command()
        async def nowe(ctx, slowo: str = None, day_info: str = '0'):
            if not await self.cog.check_perms(ctx, command_to_check="nowe"): return

            final_date = await self.reformat_date(ctx, day_info)
            dictums_data = self.cog.read_yaml("dictums.yaml")
            dictums_data[final_date] = slowo
            
            self.cog.write_yaml(dictums_data, 'dictums.yaml')
            await ctx.invoke(self.get_command("slowo"), day_info)

        @self.command(help="slowo <data lub indeks (domyślnie 0 - dziś)> Podaje słowo na dzień. Poprawny format daty to dd.mm.yy lub indeks dnia: '0' - dziś, '-1' - wczoraj itd.")
        async def slowo(ctx, day_info: 'str' = '0'):
            today = date.today()
            final_date = await self.reformat_date(ctx, day_info)
            if not final_date:
                return
            all_dictums = self.cog.read_yaml("dictums.yaml")

            chosen_dictum = all_dictums.get(final_date, False)
            if final_date != today.strftime("%d.%m.%y"):
                if chosen_dictum:
                    dictum_output = f"Archiwalne słowo na dzień {final_date}: {chosen_dictum}"
                else:
                    dictum_output = f"Brak słowa na dzień z datą {final_date} :( Archiwum jest prowadzone od {list(all_dictums.keys())[0]} do {list(all_dictums.keys())[-1]}"
            else:
                if chosen_dictum:
                    dictum_output = f"Słowo na dzień {final_date}: {chosen_dictum}"
                else:
                    chosen_dictum = all_dictums.get((today + timedelta(days=-1)).strftime("%d.%m.%y"), "Brak słowa z wczoraj?! :o")
                    dictum_output = f"Słowo na dzień {final_date} już wkrótce!\nSłowo z wczoraj: {chosen_dictum}"

            await ctx.send(dictum_output)

        @self.command(help="wyzwij <@użytkownik> Wyzywa użytkownika losowym wyzwiskiem.") 
        async def wyzwij(ctx, user: discord.User, channel_name: str = None):
            if not await self.cog.check_perms(ctx, command_to_check="wyzwij"): return
            all_insults = self.cog.read_yaml('insults.yaml')
            insult = random.choice(all_insults)

            if not channel_name:
                await ctx.send(f"{user.mention} {insult}")
            else:
                output_channel = self.get_channel(self.get_channel_id(ctx, channel_name))
                await output_channel.send(f"{user.mention} {insult}")
    
        @self.command(help="nowe_wyzwisko <'nowe wyzwisko do dodania'> Dodaje wyzwisko do listy.")
        async def nowe_wyzwisko(ctx, new_insult: str = ":("):
            if not await self.cog.check_perms(ctx, command_to_check="nowe_wyzwisko"): return

            insults_data = self.cog.read_yaml("insults.yaml")
            insults_data.append(new_insult)
            self.cog.write_yaml(insults_data, 'insults.yaml')
            await ctx.send(f"Dodano wyzwisko: {new_insult}")

        @self.command(help="lista_wyzwisk Pokazuje listę wyzwisk wraz z ich indeksem.")
        async def lista_wyzwisk(ctx):
            if not await self.cog.check_perms(ctx, command_to_check="lista_wyzwisk"): return

            insult_list = "\n".join([f"[{i}]: {insult}" for  i, insult in enumerate(self.cog.read_yaml("insults.yaml"))])
            await ctx.send(insult_list)

        @self.command(help="usun_wyzwisko <indeks wyzwiska (domyślnie -1)> Usuwa wybrane wyzwisko z listy.")
        async def usun_wyzwisko(ctx, insult_index: int =-1):
            if not await self.cog.check_perms(ctx, command_to_check="usun_wyzwisko"): return

            insults_data = self.cog.read_yaml("insults.yaml")
            deleted_insult = insults_data.pop(insult_index)
            self.cog.write_yaml(insults_data, 'insults.yaml')
            await ctx.send(f"Usunięto wyzwisko: {deleted_insult}")
        
        @self.command(help="fade fade fade")
        async def fade(ctx):
            if isinstance(ctx.message.channel, discord.DMChannel):
                await ctx.send("Tę komendę można wywołać tylko na serwerach ;)")
                return
            img_path = os.path.join('fade.jpg')
            with open(img_path, 'rb') as f:
                picture = discord.File(f, filename="fade.jpg")
            await ctx.send(file=picture)

        @self.event
        async def on_raw_reaction_add(payload):
            print("reaction add")
            if payload.message_id != WITAJ_MSG_ID: return
            if payload.user_id == bot.user.id: return

            role_emojis = self.cog.read_yaml("emojis.yaml")
            emoji = payload.emoji
             
            print(emoji)

            guild = bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = guild.get_role(role_emojis["used"].get(payload.emoji, {"role_id": None})["role_id"])
            if role:
                await member.add_roles(role)
        
        @bot.event
        async def on_raw_reaction_remove(payload):
            print("reaction remove")
            if payload.message_id != WITAJ_MSG_ID: return 
        
        @self.command(help="Edytuj wiadomość witającą.")
        async def witaj(ctx):
            if not await self.cog.check_perms(ctx, command_to_check="witaj"): return

            witaj_guild = self.get_guild(WITAJ_GUILD_ID)
            witaj_channel = self.get_channel(self.cog.get_channel_id(ctx, "test"))
            witaj_msg = await witaj_channel.fetch_message(WITAJ_MSG_ID)
            yearly_channels_category = self.get_channel(YEARLY_CHANNELS_CATEGORY_ID)

            emojis = self.cog.read_yaml("emojis.yaml")
            witaj_roles = self.cog.read_yaml("witaj_roles.yaml")
            default_roles = witaj_roles.get("default", [])
            stable_roles = witaj_roles.get("stable", [])
            yearly_roles = witaj_roles.get("yearly", [])

            today = date.today()
            todays_year = today.year if today.month > 6 else todays_year - 1
            
            new_witaj_msg_content = "Wybierz rolę zgodną ze swoim rocznikiem i etapem studiów, reagując odpowiednią emotką:\n"
            new_witaj_msg_emojis = []
            for year in range(todays_year - 2, todays_year + 1):
                mgr_enabled = year > todays_year - 2
                print(year, mgr_enabled)
                if not yearly_roles.get(year, False):
                    witaj_roles["yearly"][year] = {}
                    for stage in ["Lic", "Mgr"]:
                        new_role_emoji = random.choice(list(emojis["available"].keys()))
                        new_role_emoji_name = emojis["available"][new_role_emoji]
                        new_role_name = f"{new_role_emoji}{year}-{stage}"
                        new_role = await witaj_guild.create_role(name=new_role_name)
                        print("checkpoint1")

                        used_emoji = emojis["available"].pop(new_role_emoji)
                        print(used_emoji)
                        emojis["used"][new_role_emoji] = {"name": used_emoji, "role_id": new_role.id}

                        print("checkpoint2")
                        new_channel_overwrites = {
                            witaj_guild.default_role: discord.PermissionOverwrite(view_channel=False),
                            new_role: discord.PermissionOverwrite(view_channel=True)
                            }
                        new_channel_name = f"{new_role_name}-private"
                        new_channel_topic = f"Private war room, just for {new_role_emoji_name}"
                        new_channel = await witaj_guild.create_text_channel(name=new_channel_name,
                                                                            overwrites=new_channel_overwrites,
                                                                            topic=new_channel_topic,
                                                                            category=yearly_channels_category)
                        print("checkpoint3")
                        witaj_roles["yearly"][year][stage] = {

                            "emoji": new_role_emoji,
                            "role_id": new_role.id,
                            "channel_id": new_channel.id
                                
                            }                        
                        print(new_role_name, new_channel_name, new_channel_topic)
                
                # print("checkpoint4", witaj_roles)
                lic_emoji = witaj_roles["yearly"][year]["Lic"]["emoji"]
                new_witaj_msg_emojis.append(lic_emoji)
                new_witaj_msg_content += f"{lic_emoji}:   {year}-Lic\n"
                print("checkpoint5")
                if mgr_enabled:
                    mgr_emoji = witaj_roles["yearly"][year]["Mgr"]["emoji"]
                    new_witaj_msg_content += f"{mgr_emoji}:   {year}-Mgr\n"
                    new_witaj_msg_emojis.append(mgr_emoji)
                

            else:
                new_witaj_msg_content += "Jeśli interesują Cię inne role niezwiązane z rocznikiem, wybierz odpowiednią etmokę:\n"
                for stable_role_name in stable_roles:
                    stable_role_emoji = stable_roles[stable_role_name]["emoji"]
                    new_witaj_msg_content += f"{stable_role_emoji}:   {stable_role_name}\n"
                    new_witaj_msg_emojis.append(stable_role_emoji)
            
            

            self.cog.write_yaml(emojis, 'emojis.yaml')
            self.cog.write_yaml(witaj_roles, "witaj_roles.yaml")


            
            await witaj_msg.edit(content=new_witaj_msg_content)
            print(new_witaj_msg_emojis)
            for emoji in new_witaj_msg_emojis:
                await witaj_msg.add_reaction(emoji)


bot = BdellovibrioBot()

bot.run(TOKEN)
