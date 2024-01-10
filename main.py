import discord
from discord.ext import commands
import os
# import infer_bot as rvc
import yt_dlp as youtube_dl
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='^', intents=intents)

with open("key", 'r') as f:
    token = f.read()

async def load_extensions():
    with open("extensions.txt", 'r') as f:
        for extension in f:
            await bot.load_extension("src." + extension.strip('\n'))

@bot.event
async def on_ready():
    await load_extensions()
    status_w = discord.Status.online
    activity_w = discord.Activity(type=discord.ActivityType.playing, name="osu!")
    # rvc.vc_setup()
    # rvc.uvr_setup()

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
    try:
        bot.load_extension("src." + extension.lower())
        await ctx.send(f"{extension} loaded.")
    except Exception as e:
        await ctx.send(e)

@bot.command(help="Un-load extension.", brief="Un-load extension.")
async def unload(ctx, extension):
    try:
        bot.unload_extension("src." + extension.lower())
        await ctx.send(f"{extension} unloaded.")
    except Exception as e:
        await ctx.send(e)

@bot.command(help="Re-load extension.", brief="Re-load extension.")
async def reload(ctx, extension):
    try:
        bot.reload_extension("src." + extension.lower())
        await ctx.send(f"{extension} reloaded")
    except Exception as e:
        await ctx.send(e)

@bot.command(help="Sync commands. Can only be used by owner", brief="Sync commands.")
async def sync(ctx):
    if ctx.author.id == 551017766920912907:
        await bot.tree.sync()
        await ctx.send("Synced!")
    else:
        await ctx.send("You are not the owner!")

@bot.command(help="Download audio from youtube. format: mp3", brief="Download audio from youtube.")
async def download(ctx, url: str):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'downloads/temp.%(ext)s'
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            await ctx.send("Downloading...")
            ydl.download([url])
            await ctx.send(file=discord.File("downloads/temp.mp3"))
            await ctx.send("Downloaded!")
            os.remove("downloads/temp.mp3")
        except:
            await ctx.send("Error!")

@bot.command(help="make Nyan sing using AI!", brief="sing!")
async def sing(ctx):
    

@bot.tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f'{round(bot.latency * 1000)} (ms)')

@bot.tree.command(name="hello")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hi, {interaction.user.mention}! Nice to meet you!")

@bot.tree.command(name="download", description="Download audio from youtube.")
async def download(interaction: discord.Interaction, url: str):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'downloads/temp.%(ext)s'
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            await interaction.response.send_message("Downloading...")
            ydl.download([url])
            await interaction.response.send_message(file=discord.File("downloads/temp.mp3"))
            await interaction.response.send_message("Downloaded!")
            os.remove("downloads/temp.mp3")
        except:
            await interaction.response.send_message("Error!")
    
bot.run(token)