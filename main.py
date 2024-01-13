import shutil
import discord
from discord.ext import commands
import os
import infer_bot as rvc

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='^', intents=intents)

owner_id = 551017766920912907
guild_id = discord.Object(id=931487348196245524)

with open("key", 'r') as f:
    token = f.read()

async def load_ext():
    for filename in os.listdir('./ext'):
        if filename.endswith('.py'):
            print(f"loading {filename}")
            await bot.load_extension(f'ext.{filename[:-3]}')

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    await load_ext()
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

@bot.command(help="Reload extension.", brief="Re-load extension.")
async def reload(ctx, extension):
    if ctx.author.id != owner_id:
        await ctx.send("You are not the owner!")
        return
    try:
        await bot.reload_extension("ext." + extension.lower())
        await ctx.send(f"{extension} reloaded")
    except Exception as e:
        await ctx.send(e)

@bot.command(help="Sync commands to test guild. Can only be used by owner", brief="Sync commands.")
async def sync_guild(ctx):
    if ctx.author.id == owner_id:
        bot.tree.copy_global_to(guild=guild_id)
        synced = await bot.tree.sync(guild=guild_id)
        # print(f"Synced {len(synced)} command(s).")
        await ctx.send(f"Synced {len(synced)} command(s).")
        for command in synced:
            await ctx.send(command.name)
    else:
        await ctx.send("You are not the owner!")

@bot.command(help="Sync global commands. Can only be used by owner", brief="Sync commands.")
async def sync(ctx):
    if ctx.author.id == owner_id:
        synced = await bot.tree.sync()
        # print(f"Synced {len(synced)} command(s).")
        await ctx.send(f"Synced {len(synced)} command(s).")
    else:
        await ctx.send("You are not the owner!")


@bot.tree.command(name="ping", description="Get bot latency.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f'{round(bot.latency * 1000)} (ms)')

bot.run(token)