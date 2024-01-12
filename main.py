import shutil
import discord
from discord.ext import commands
import os
import infer_bot as rvc
import yt_dlp as youtube_dl
import time
from pydub import AudioSegment
from scipy.io.wavfile import write

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='^', intents=intents)
owner_id = 551017766920912907

with open("key", 'r') as f:
    token = f.read()

async def load_extensions():
    with open("extensions.txt", 'r') as f:
        for extension in f:
            await bot.load_extension("ext." + extension.strip('\n'))


@bot.event
async def on_ready():
    await bot.wait_until_ready()
    await load_extensions()
    status_w = discord.Status.online
    activity_w = discord.Activity(type=discord.ActivityType.playing, name="Team Fortress 2")
    await bot.change_presence(status=status_w, activity=activity_w)
    print("Ready!")
    print("User name:", bot.user.name)
    print("User ID:", bot.user.id)

@bot.event
async def on_message(message):
    if message.author.id == bot.user.id:
        return
    # print(message.author.id)
    await bot.process_commands(message)

@bot.command(help="Load extension.", brief="Load extension.")
async def load(ctx, extension):
    if ctx.author.id != owner_id:
        await ctx.send("You are not the owner!")
        return
    try:
        bot.load_extension("src." + extension.lower())
        await ctx.send(f"{extension} loaded.")
    except Exception as e:
        await ctx.send(e)

@bot.command(help="Un-load extension.", brief="Un-load extension.")
async def unload(ctx, extension):
    if ctx.author.id != owner_id:
        await ctx.send("You are not the owner!")
        return
    try:
        bot.unload_extension("src." + extension.lower())
        await ctx.send(f"{extension} unloaded.")
    except Exception as e:
        await ctx.send(e)

@bot.command(help="Re-load extension.", brief="Re-load extension.")
async def reload(ctx, extension):
    if ctx.author.id != owner_id:
        await ctx.send("You are not the owner!")
        return
    try:
        bot.reload_extension("src." + extension.lower())
        await ctx.send(f"{extension} reloaded")
    except Exception as e:
        await ctx.send(e)

@bot.command(help="Sync commands. Can only be used by owner", brief="Sync commands.")
async def sync(ctx):
    if ctx.author.id == owner_id:
        await bot.tree.sync()
        await ctx.send("Synced!")
    else:
        await ctx.send("You are not the owner!")


@commands.tree.command(name="ping", description="Get bot latency.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f'{round(bot.latency * 1000)} (ms)')

    
bot.run(token)