import shutil
import discord
from discord import app_commands
from discord.ext import commands
import os
import infer_bot as rvc
import yt_dlp as youtube_dl
import time
from pydub import AudioSegment
from scipy.io.wavfile import write

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
        try:      
            if ydl.extract_info(url, download=False)['duration'] > 300:
                raise Exception("Video too long!")      
            # print("\n\n\n\n\n Downloading... \n\n\n\n\n")
            ydl.download(url)
        except:
            # print("\n\n\n\n\n Error occured during downloading. \n\n\n\n\n")
            raise Exception("Error occured during downloading.")
    return

class audio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_converter = rvc.voice_converter()
        self.voice_converter.change_sid()
                
    @commands.command(help="Download audio from youtube. format: mp3", brief="Download audio from youtube.")
    async def download(self, ctx, url: str):
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
            download_audio(url, id)
        except:
            embed.title = "Error!"
            embed.description = "Error occured during downloading. Maybe the video is too long. (Max: 300s), or the url is not available."
            await ctx.send(embed=embed)
            if os.path.exists(f"audio/{id}"):
                shutil.rmtree(f"audio/{id}")
            return
        try:
            end_time = time.perf_counter()
            embed.title = "Downloaded!"
            embed.description = f"Audio successfully downloaded under {round(end_time - start_time, 2)}s."
            await ctx.send(embed=embed,file=discord.File(f"audio/{id}/download.mp3"))
            shutil.rmtree(f"audio/{id}")
            # os.remove("audio/raw/temp.mp3")
        except:
            embed.title = "Error!"
            embed.description = "Error occured during downloading. Maybe the video is too long. (Max: 300s), or the url is not available."
            shutil.rmtree(f"audio/{id}")
            await ctx.send(embed=embed)
        

    @commands.command(help="make Nyan sing using AI! add transpose value after url (default: 0)", brief="make Nyan sing using AI!")
    async def sing(self, ctx, url: str, transpose: float = 0):
        id = ctx.message.id
        path = os.getcwd()
        if url == "":
            await ctx.send("Please input a url.")
            return
        await ctx.send("Downloading audio...")
        start_time = time.perf_counter()
        try:
            await download_audio(url, id=id, filename=str(id), format="wav")
            await ctx.send("Extracting vocal...")
            try:
                await self.voice_converter.vocal_extract(dir_wav_input=f"{path}\\audio\\{id}",
                                            opt_ins_root=f"{path}\\audio\\{id}",
                                            opt_vocal_root=f"{path}\\audio\\{id}",)
            except:
                await ctx.send("Error during vocal extraction!")
                shutil.rmtree(f"audio/{id}")
                return
            await ctx.send("Forcing Nyan to sing...")

            try:
                res = await self.voice_converter.infer(vc_transform0=transpose, input_audio0=f"audio/{id}/vocal_{id}.wav.reformatted.wav_10.wav")
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

   

async def setup(bot):
    await bot.add_cog(audio(bot))
