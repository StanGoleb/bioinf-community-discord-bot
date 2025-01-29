import os
import re
import random
import time
from datetime import date, timedelta
import json
import asyncio
import discord
from dotenv import load_dotenv
from discord.ext import commands
from discord import SlashCommand
from discord import ButtonStyle, Button

load_dotenv('./tokens.env')
DIS_TOKEN = os.getenv('DISCORD_TOKEN')
CHAT_BOT_ID=int(os.getenv('BOT_ID'))

INTENTS = discord.Intents.all()
INTENTS.messages = True


bot = commands.Bot(command_prefix='%', intents=INTENTS)

async def find_id(ctx, chat_name):
        with open('../ids/chat_ids.json') as jfile:
                chat_ids = json.load(jfile)
        if chat_name in chat_ids:
                return chat_ids[chat_name]

        else:
                available_channels = ', '.join(chat_ids.keys())
                err_msg = f'zła nazwa kanału: {chat_name} \n Dostepne nazwy to {available_channels}'
                await ctx.send(err_msg)
                return False

async def check_permission(ctx, command):
        with open(f'../permissions/{command}.json') as jfile:
                permitted = json.load(jfile)
                name = ctx.message.author.name
                if name in permitted:
                        return True
                else:
                        await ctx.send(f'Nie masz dostępu do komendy {command}')
                        return False



#================================================================================
@bot.command()
async def plyny(ctx):
	with open('./plyny.json', encoding='utf-8') as jfile:
		data = json.load(jfile)
	piwo = random.choice(data)
	await ctx.send(piwo)

@bot.command()
async def dodaj_plyny(ctx, new_plyn):
	await check_permission(ctx, 'dodaj_plyny')
	with open('./plyny.json', 'r+') as jfile:
		data = json.load(jfile)
		data.append(new_plyn)
		jfile.seek(0)
		json.dump(data, jfile, indent = 4)
	await ctx.send(f'Dodano nowy plyn: {new_plyn}')


@bot.command()
async def czatuj(ctx, message, chat_name='druciaki'):
        await check_permission(ctx, 'czatuj')
        curr_room = bot.get_channel(await find_id(ctx, chat_name))
        if curr_room:
                await curr_room.send(message)

bot.run(DIS_TOKEN, reconnect=True)
