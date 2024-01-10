import discord
from discord.ext import commands
import os
import infer_bot as rvc
import yt_dlp as youtube_dl
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
    activity_w = discord.Activity(type=discord.ActivityType.playing, name="osu!")
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

def download_audio(url: str):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'audio/temp.%(ext)s'
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        if ydl.extract_info(url, download=False)['duration'] > 300:
            return False
        try:            
            ydl.download([url])
            return True
        except:
            return False
            
@bot.command(help="Download audio from youtube. format: mp3", brief="Download audio from youtube.")
async def download(ctx, url: str):
    if url == "":
        await ctx.send("Please input a url.")
        return
    await ctx.send("Downloading...")
    result = download_audio(url)
    if result:
        await ctx.send(file=discord.File("audio/temp.mp3"))
        await ctx.send("Downloaded!")
        # os.remove("audio/raw/temp.mp3")
    else:
        await ctx.send("Error!")
    

@bot.command(help="make Nyan sing using AI!", brief="sing!")
async def sing(ctx, url: str, transpose: float = 0):
    if url == "":
        await ctx.send("Please input a url.")
        return
    await ctx.send("Downloading audio...")
    result = download_audio(url)
    if result:
        await ctx.send("Extracting vocal...")
        try:
            voice_converter.vocal_extract()
        except:
            await ctx.send("Error during vocal extraction!")
            return
        await ctx.send("Forcing Nyan to sing...")
        try:
            res = voice_converter.infer(vc_transform0=transpose, input_audio0="opt\\vocal_temp.mp3.reformatted.wav_10.wav")
        except:
            await ctx.send("Error during inference!")
            return
        await ctx.send("Recording...")

        from scipy.io.wavfile import write
        import wave
        try:
            rate = res[0]
            write('audio/cover.wav', rate, res[1])
            infiles = ["audio/cover.wav", "opt\\instrument_temp.mp3.reformatted.wav_10.wav"]
            outfile = "result.wav"

            data= []
            for infile in infiles:
                w = wave.open(infile, 'rb')
                data.append( [w.getparams(), w.readframes(w.getnframes())] )
                w.close()

            output = wave.open(outfile, 'wb')
            output.setparams(data[0][0])
            output.writeframes(data[0][1])
            output.writeframes(data[1][1])
            output.close()

            await ctx.send(file=discord.File("result.wav"))
            await ctx.send("Nyan finished singing!")
        except:
            await ctx.send("Error during file writing!")
            return
        # # os.remove("audio/raw/temp.mp3")
    else:
        await ctx.send("Error!")
    

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