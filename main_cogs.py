import os
import re
import random
import discord
from discord.ext import commands, tasks
from datetime import date, timedelta
from dotenv import load_dotenv
import ruamel.yaml

class MainCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def read_yaml(self, path):
        yaml = ruamel.yaml.YAML()
        with open(path, encoding="utf-8") as yfile:
            data = yaml.load(yfile)
        return data

    def write_yaml(self, data, path):
        yaml = ruamel.yaml.YAML()
        yaml.width = 4096
        yaml.preserve_quotes = True
        with open(path, "w", encoding="utf-8") as yfile:
            yaml.dump(data, yfile)

    def get_merged_permissions(self):
        wide_permissions = self.read_yaml('../../helper_files/wide_permissions.yaml')
        bot_permissions = self.read_yaml('permissions.yaml')

        combined = {"roles": {}, "users": {}}
        for permission_data in [wide_permissions, bot_permissions]:
            for cat in combined:
                for key in permission_data.get(cat, []):
                    combined[cat][key] = list(set(combined[cat].get(key, set())) | set(permission_data[cat][key]))
                    
        return combined

    def get_admin_ids(self):
        combined_permissions = self.get_merged_permissions()
        return combined_permissions["users"].get("admin", [])
    
    def get_available_channels(self, ctx):
        channels_info = self.read_yaml('../../helper_files/channel_ids.yaml')

        if isinstance(ctx.message.channel, discord.DMChannel):
            user_roles = []
        else:
            user_roles = ctx.message.author.roles

        user_id = ctx.message.author.id

        admin_ids = self.get_admin_ids()

        available_channels = {}
        for channel_name, channel in channels_info.items():
            channel_permission = channel["required_permission"]

            if self.bot.bot_perm >= channel_permission["bots"]:
                if any(role.id in channel_permission["roles"] for role in user_roles) or (user_id in channel_permission["users"]) or (user_id in admin_ids) or ("all" in channel_permission["roles"]):
                    available_channels[channel_name] = channel

        return available_channels
    
    def get_channel_id(self, ctx, channel_name: str = None):
        return self.get_available_channels(ctx).get(channel_name, {}).get("id", None)

    async def check_channel_permission(self, ctx, channel_to_check: str = None, silent=False):
        if self.get_available_channels(ctx).get(channel_to_check, False):
            return True
        
        if not silent:
            await ctx.send(f"Ty lub bot nie macie uprawnień do kanału {channel_to_check}. Użyj `{self.bot.command_prefix}kanaly` by sprawdzić te dostępne.")
        
        return False

    async def check_command_permission(self, ctx, command_to_check: str = None, silent=False):
        combined_permissions = self.get_merged_permissions()
        if isinstance(ctx.message.channel, discord.DMChannel):
            user_roles = []
        else:
            user_roles = ctx.message.author.roles

        user_id = ctx.message.author.id

        if not self.bot.get_command(command_to_check):
            await ctx.send("Komenda {command_to_check} nie istnieje.")
            return False

        # If command's permissions aren't specified, it's permitted to all
        if command_to_check not in combined_permissions["roles"] and command_to_check not in combined_permissions["users"]:
            return True

        for i in ["admin", command_to_check]:
            if user_id in combined_permissions["users"].get(i, []):
                return True

        for role in user_roles:
            if role.id in combined_permissions["roles"].get(command_to_check, []):
                return True
        
        if not silent:
            await ctx.send(f"Nie masz uprawnień do komendy {command_to_check}.")
        
        return False
    
    async def check_perms(self, ctx, command_to_check: str = None, channel_to_check: str = None, silent=False):
        command_perm = await self.check_command_permission(ctx, command_to_check) if command_to_check else True
        channel_perm = await self.check_channel_permission(ctx, channel_to_check) if channel_to_check else True
        return command_perm and channel_perm

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f"Taka komenda nie istnieje. Sprawdź dostępne komendy za pomocą {self.bot.command_prefix}help.")
        else:
            command_name = ctx.command.name if ctx.command else None
            if command_name:
                    if isinstance(ctx.message.channel, discord.DMChannel):
                        print(error)
                        await ctx.send(error)
                        await ctx.send("Część komend nie działa w DMach :o Jeśli uważasz, że to błąd, skontaktuj się z twórcą.")
                    else:
                        print(error)
                        await ctx.send(f"Wystąpił błąd podczas wywoływania {command_name}. Upewnij się, że używasz jej zgodnie z instrukcją:")
                        await ctx.invoke(self.bot.get_command("help"), command_to_help=command_name)

            else:
                await ctx.send("Nieznany błąd @Stasiek")

    @commands.command(help="help <komenda (domyślnie wszystkie)> Wyświetla opis komend(y)")
    async def help(self, ctx, command_to_help: str = None):
        if command_to_help:
            if await self.check_command_permission(ctx, command_to_help):
                await ctx.send(self.bot.get_command(command_to_help).help)
        else:
            output = f"\n====================================================\nWszystkie komendy {self.bot.bot_name} dostępne dla Ciebie:\n"
            for command in self.bot.commands:
                if await self.check_command_permission(ctx, command.name, silent=True):
                    output += f"\n`{command.name}`: {command.help if command.help else 'brak opisu'}\n"
            output += "===================================================="
            await ctx.send(output)

    @commands.command(help="Pong!")
    async def ping(self, ctx):
        await ctx.send("Pong!")

    @commands.command(help="Wyświetla dostępne kanały dla aktualnego bota i użytkownika")
    async def kanaly(self, ctx):
        available_channels = [channel_name for channel_name in self.get_available_channels(ctx)]
        await ctx.send(f"Kanały dostępne dla {ctx.author.name} i {self.bot.bot_name} to:\n {f', '.join(available_channels)}")

    @commands.command(help='czatuj <"twoja wiadomość"> <kanał (domyślnie test)>')
    async def czatuj(self, ctx, message: str = None, channel: str = "test"):
        if not await self.check_perms(ctx, "czatuj", channel): return

        output_channel = self.bot.get_channel(self.get_channel_id(ctx, channel))
        await output_channel.send(message)

async def setup(bot):
    bot.remove_command('help')
    await bot.add_cog(MainCommands(bot))
