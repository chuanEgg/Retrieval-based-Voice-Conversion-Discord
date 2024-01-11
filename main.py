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

with open("key", 'r') as f:
    token = f.read()

async def load_extensions():
    with open("extensions.txt", 'r') as f:
        for extension in f:
            await bot.load_extension("src." + extension.strip('\n'))

voice_converter = rvc.voice_converter()
voice_converter.change_sid()

@bot.event
async def on_ready():
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

def download_audio(url: str, id: str, filename: str = "download", format: str = "mp3"):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': format,
            'preferredquality': '192',
        }],
        'outtmpl': f'audio/{id}/{filename}.%(ext)s'
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        if ydl.extract_info(url, download=False)['duration'] > 300:
            return "Audio is too long!"
        try:            
            ydl.download([url])
            return "Success!"
        except:
            return "Error!"
            
@bot.command(help="Download audio from youtube. format: mp3", brief="Download audio from youtube.")
async def download(ctx, url: str):
    id = ctx.message.id
    embed = discord.Embed(title="Downloading...", description="Please wait.", color=0x4287f5)
    if url == "":
        embed.description = "Please input a url."
        embed.title = "Error!"
        await ctx.send(embed=embed)
        return
    await ctx.send(embed=embed)
    start_time = time.perf_counter()
    try:
        await download_audio(url, id)
        end_time = time.perf_counter()
        embed.title = "Downloaded!"
        embed.description = f"Audio successfully downloaded under {end_time - start_time}s."
        await ctx.send(embed=embed,file=discord.File(f"audio/{id}/download.mp3"))
        shutil.rmtree(f"audio/{id}")
        # os.remove("audio/raw/temp.mp3")
    except:
        embed.title = "Error!"
        embed.description = "Error occured during downloading. Maybe the video is too long. (Max: 300s), or the url is not available."
        await ctx.send(embed=embed)
    

@bot.command(help="make Nyan sing using AI! add transpose value after url (default: 0)", brief="make Nyan sing using AI!")
async def sing(ctx, url: str, transpose: float = 0):
    id = ctx.message.id
    path = os.getcwd()
    if url == "":
        await ctx.send("Please input a url.")
        return
    await ctx.send("Downloading audio...")
    start_time = time.perf_counter()
    try:
        download_audio(url, id=id, filename=str(id), format="wav")
        await ctx.send("Extracting vocal...")
        try:
            voice_converter.vocal_extract(dir_wav_input=f"{path}\\audio\\{id}",
                                          opt_ins_root=f"{path}\\audio\\{id}",
                                          opt_vocal_root=f"{path}\\audio\\{id}",)
        except:
            await ctx.send("Error during vocal extraction!")
            shutil.rmtree(f"audio/{id}")
            return
        await ctx.send("Forcing Nyan to sing...")

        try:
            res = voice_converter.infer(vc_transform0=transpose, input_audio0=f"audio/{id}/vocal_{id}.wav.reformatted.wav_10.wav")
        except:
            await ctx.send("Error during inference!")
            shutil.rmtree(f"audio/{id}")
            return
        await ctx.send("Recording...")

        try:
            rate = res[0]
            write(f'audio/{id}/cover.wav', rate, res[1])
            vocal = AudioSegment.from_wav(f"audio/{id}/cover.wav")
            instrument = AudioSegment.from_wav(f"audio/{id}/instrument_{id}.wav.reformatted.wav_10.wav")
            vocal = vocal + 9
            result = instrument.overlay(vocal)
            result.export(f"audio/{id}/result.mp3", format="mp3")
            await ctx.send(file=discord.File(f"audio/{id}/result.mp3"))
            end_time = time.perf_counter()
            await ctx.send(f"Nyan finished singing under {round(end_time - start_time, 2)} s.")
        except:
            await ctx.send("Error during file writing!")
            shutil.rmtree(f"audio/{id}")
            return
        # # os.remove("audio/raw/temp.mp3")
        shutil.rmtree(f"audio/{id}")
    except:
        await ctx.send("Error!")
        shutil.rmtree(f"audio/{id}")
        return
    

@bot.tree.command(name="ping", description="Get bot latency.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f'{round(bot.latency * 1000)} (ms)')

@bot.tree.command(name="download", description="Download audio from youtube.")
async def download(interaction: discord.Interaction, url: str):
    id = interaction.message.id
    embed = discord.Embed(title="Downloading...", description="Please wait.", color=0x4287f5)
    if url == "":
        embed.description = "Please input a url."
        embed.title = "Error!"
        await interaction.response.send_message(embed=embed)
        return
    await interaction.response.send_message(embed=embed)
    start_time = time.perf_counter()
    try:
        await download_audio(url, id=id)
        end_time = time.perf_counter()
        embed.title = "Downloaded!"
        embed.description = f"Audio successfully downloaded under {round(end_time - start_time, 2)} s."
        await interaction.response.edit_message(embed=embed,file=discord.File(f"audio/{id}/temp.mp3"))
        shutil.rmtree(f"audio/{id}")
        # os.remove("audio/raw/temp.mp3")
    except:
        embed.title = "Error!"
        embed.description = "Error occured during downloading. Maybe the video is too long. (Max: 300s), or the url is not available."
        await interaction.response.edit_message(embed=embed)

@bot.tree.command(name="sing", description="Make Nyan sing using AI!")
async def sing(interaction: discord.Interaction, url: str, transpose: int = 0):
    embed = discord.Embed(title="Downloading audio...", description="Please wait.", color=0x4287f5)
    id = interaction.message.id
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
        await interaction.response.edit_message(embed=embed)
        try:
            voice_converter.vocal_extract(dir_wav_input=f"{path}\\audio\\{id}",
                                          opt_ins_root=f"{path}\\audio\\{id}",
                                          opt_vocal_root=f"{path}\\audio\\{id}",)
        except:
            embed.title = "Error!"
            embed.description = "Error occured during vocal extraction!"
            await interaction.response.edit_message(embed=embed)
            shutil.rmtree(f"audio/{id}")
            return
        
        embed.title = "Forcing Nyan to sing..."
        await interaction.response.edit_message(embed=embed)
        try:
            res = voice_converter.infer(vc_transform0=transpose, input_audio0=f"audio/{id}/vocal_{id}.wav.reformatted.wav_10.wav")
        except:
            embed.title = "Error!"
            embed.description = "Error occured during inference!"
            await interaction.response.edit_message(embed=embed)
            shutil.rmtree(f"audio/{id}")
            return
        
        embed.title = "Recording..."
        await interaction.response.edit_message(embed=embed)

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
            await interaction.response.edit_message(embed=embed, file=discord.File(f"audio/{id}/result.mp3"))
            shutil.rmtree(f"audio/{id}")
        except:
            embed.title = "Error!"
            embed.description = "Error occured during file writing!"
            shutil.rmtree(f"audio/{id}")
            await interaction.response.edit_message(embed=embed)
            return
        # # os.remove("audio/raw/temp.mp3")
    except:
        embed.title = "Error!"
        embed.description = "Error occured during downloading. Maybe the video is too long. (Max: 300s)"
        try:
            shutil.rmtree(f"audio/{id}")
        except:
            pass
        await interaction.response.edit_message(embed=embed)
    
bot.run(token)