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
            if ydl.extract_info(url, download=False)['duration'] > 200:
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
                
    @app_commands.command(name="download", description="Download audio from youtube.")
    async def download(self, interaction: discord.Interaction, url: str):
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
            embed.description = "Error occured during downloading. Maybe the video is too long. (Max: 200s), or the url is not available."
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
            embed.description = "Error occured during downloading. Maybe the video is too long. (Max: 200s), or the url is not available."
            shutil.rmtree(f"audio/{id}")
            await interaction.edit_original_response(embed=embed)

    @app_commands.command(name="sing", description="Make Nyan sing using AI!")
    async def sing(self, interaction: discord.Interaction, url: str, transpose: int = 0, protect: float = 0.33):
        embed = discord.Embed(title="Downloading audio...", description="Please wait.", color=0x4287f5, url=url)
        id = interaction.id
        path = os.getcwd()
        await interaction.response.send_message(embed=embed)
        start_time = time.perf_counter()
        try:
            download_audio(url, id=id, filename=str(id), format="wav")
            embed.title = "Extracting vocal..."
            await interaction.edit_original_response(embed=embed)
            try:
                self.voice_converter.vocal_extract(dir_wav_input=f"{path}\\audio\\{id}",
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
                res = self.voice_converter.infer(vc_transform0=transpose, 
                                                 input_audio0=f"audio/{id}/vocal_{id}.wav.reformatted.wav_10.wav",
                                                 protect0=protect)
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
            embed.description = "Error occured during downloading. Maybe the video is too long. (Max: 300s), or the url is not available."
            try:
                shutil.rmtree(f"audio/{id}")
            except:
                pass
            await interaction.edit_original_response(embed=embed)


async def setup(bot):
    await bot.add_cog(audio(bot))
