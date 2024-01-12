import shutil
import discord
from discord.ext import commands
import os
import infer_bot as rvc
import yt_dlp as youtube_dl
import time
from pydub import AudioSegment
from scipy.io.wavfile import write
from ext.audio import download_audio

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='^', intents=intents)
owner_id = 551017766920912907

voice_converter = rvc.voice_converter()
voice_converter.change_sid()

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

@bot.command(help="Sync commands. Can only be used by owner", brief="Sync commands.")
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

@bot.tree.command(name="download", description="Download audio from youtube.")
async def download(interaction: discord.Interaction, url: str):
    id = interaction.id
    embed = discord.Embed(title="Downloading...", description="Please wait.", color=0x4287f5)
    if url == "":
        embed.description = "Please input a url."
        embed.title = "Error!"
        await interaction.response.send_message(embed=embed)
        return
    await interaction.response.send_message(embed=embed)
    start_time = time.perf_counter()
    try:
        download_audio(url, id)
    except:
        embed.title = "Error!"
        embed.description = "Error occured during downloading. Maybe the video is too long. (Max: 300s), or the url is not available."
        await interaction.edit_original_response(embed=embed)
        if os.path.exists(f"audio/{id}"):
            shutil.rmtree(f"audio/{id}")
        return
    try:
        end_time = time.perf_counter()
        embed.title = "Downloaded!"
        embed.description = f"Audio successfully downloaded under {round(end_time - start_time, 2)} s."
        await interaction.edit_original_response(embed=embed)
        await interaction.followup.send(file=discord.File(f"audio/{id}/download.mp3"))
        shutil.rmtree(f"audio/{id}")
        # os.remove("audio/raw/temp.mp3")
    except:
        embed.title = "Error!"
        embed.description = "Error occured during downloading. Maybe the video is too long. (Max: 300s), or the url is not available."
        shutil.rmtree(f"audio/{id}")
        await interaction.edit_original_response(embed=embed)

@bot.tree.command(name="sing", description="Make Nyan sing using AI!")
async def sing(interaction: discord.Interaction, url: str, transpose: int = 0):
    embed = discord.Embed(title="Downloading audio...", description="Please wait.", color=0x4287f5)
    id = interaction.id
    path = os.getcwd()
    if url == "":
        embed.description = "Please input a url."
        embed.title = "Error!"
        await interaction.response.send_message(embed=embed)
        return
    await interaction.response.send_message(embed=embed)
    start_time = time.perf_counter()
    try:
        download_audio(url, id=id, filename=str(id), format="wav")
        embed.title = "Extracting vocal..."
        await interaction.edit_original_response(embed=embed)
        try:
            await voice_converter.vocal_extract(dir_wav_input=f"{path}\\audio\\{id}",
                                        opt_ins_root=f"{path}\\audio\\{id}",
                                        opt_vocal_root=f"{path}\\audio\\{id}",)
        except:
            embed.title = "Error!"
            embed.description = "Error occured during vocal extraction!"
            await interaction.edit_original_response(embed=embed)
            shutil.rmtree(f"audio/{id}")
            return
        
        embed.title = "Forcing Nyan to sing..."
        await interaction.edit_original_response(embed=embed)
        try:
            res = await voice_converter.infer(vc_transform0=transpose, input_audio0=f"audio/{id}/vocal_{id}.wav.reformatted.wav_10.wav")
        except:
            embed.title = "Error!"
            embed.description = "Error occured during inference!"
            await interaction.edit_original_response(embed=embed)
            shutil.rmtree(f"audio/{id}")
            return
        
        embed.title = "Recording..."
        await interaction.edit_original_response(embed=embed)

        try:
            rate = res[0]
            write(f'audio/{id}/cover.wav', rate, res[1])
            vocal = AudioSegment.from_wav(f"audio/{id}/cover.wav")
            instrument = AudioSegment.from_wav(f"audio/{id}/instrument_{id}.wav.reformatted.wav_10.wav")
            vocal = vocal + 9
            result = instrument.overlay(vocal)
            result.export(f"audio/{id}/result.mp3", format="mp3")
            end_time = time.perf_counter()
            embed.title = "Finished!"
            embed.description = f"Nyan finished singing under {round(end_time - start_time, 2)} s."
            await interaction.edit_original_response(embed=embed)
            await interaction.followup.send(file=discord.File(f"audio/{id}/result.mp3"))
            shutil.rmtree(f"audio/{id}")
        except:
            embed.title = "Error!"
            embed.description = "Error occured during file writing!"
            shutil.rmtree(f"audio/{id}")
            await interaction.edit_original_response(embed=embed)
            return
        # # os.remove("audio/raw/temp.mp3")
    except:
        embed.title = "Error!"
        embed.description = "Error occured during downloading. Maybe the video is too long. (Max: 300s)"
        try:
            shutil.rmtree(f"audio/{id}")
        except:
            pass
        await interaction.edit_original_response(embed=embed)

bot.run(token)