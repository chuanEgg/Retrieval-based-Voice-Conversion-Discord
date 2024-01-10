import discord
from discord.ext import commands
import os
import infer_bot as rvc
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='^', intents = intents)

with open("key", 'r') as f:
    token = f.read()
    # print(token)

async def load_extensions():
    with open("extensions.txt", 'r') as f:
        for extension in f:
            await bot.load_extension("src." + extension.strip('\n'))

@bot.event
async def on_ready():
    await load_extensions()
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} command(s)")
    status_w = discord.Status.online
    activity_w = discord.Activity(type=discord.ActivityType.watching, name="chuan's YouTube")
    rvc.vc_setup()
    rvc.uvr_setup()

    await bot.change_presence(status=status_w, activity=activity_w)
    print("Ready!")
    print("User name:", bot.user.name)
    print("User ID:", bot.user.id)

@bot.event
async def on_message(message):
    if message.author.id == bot.user.id:
        return

    if "hello" in message.content.lower():
        await message.channel.send("Hello~ Nice to meet you.")

    if message.content.lower().startswith("help"):
        await message.channel.send("Enter commands starting with $ or enter $ for more information:)")
    if "好電" in message.content or "電欸" in message.content or "電ㄟ" in message.content:
        await message.channel.send(f"{message.author.mention}好電:zap:")

    await bot.process_commands(message)

@bot.command(help = "Load extension.", brief = "Load extension.")
async def load(ctx, extension):
    try:
        bot.load_extension("src." + extension.lower())
        await ctx.send(f"{extension} loaded.")
    except Exception as e:
        await ctx.send(e)

@bot.command(help = "Un-load extension.", brief = "Un-load extension.")
async def unload(ctx, extension):
    try:
        bot.unload_extension("src." + extension.lower())
        await ctx.send(f"{extension} unloaded.")
    except Exception as e:
        await ctx.send(e)

@bot.command(help = "Re-load extension.", brief = "Re-load extension.")
async def reload(ctx, extension):
    try:
        bot.reload_extension("src." + extension.lower())
        await ctx.send(f"{extension} reloaded")
    except Exception as e:
        await ctx.send(e)

@bot.tree.command(name = "ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f'{round(bot.latency * 1000)} (ms)')

@bot.tree.command(name = "hello")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hi, {interaction.user.mention}! Nice to meet you!")

bot.run(token)