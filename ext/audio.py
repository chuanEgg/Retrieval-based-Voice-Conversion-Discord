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
from typing import List

def download_audio(url: str, id: str, filename: str = "download", format: str = "mp3"):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': format,
            'preferredquality': '192',
        }],
        'outtmpl': f'audio/{id}/{filename}.%(ext)s',
        'quiet': True
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download(url)
        except:
            pass

def check_url_video(url):
    ydl = youtube_dl.YoutubeDL({'quiet': True})
    try:
        info = ydl.extract_info(url, download=False)
        if info['duration'] > 200:
            return [False, "Video too long!"]
        return [True, None]
    except Exception:
        return [False, "Invalid URL!"]

class audio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_converter = rvc.voice_converter()
        self.voice_converter.change_sid()
                
    @app_commands.command(name="download", description="Download audio from youtube.")
    @app_commands.describe(url = "Youtube URL to download.")
    async def download(self, interaction: discord.Interaction, url: str):
        id = interaction.id
        check = check_url_video(url)
        if check[0] == False:
            await interaction.response.send_message(check[1])
            return
        embed = discord.Embed(title="Downloading...", description="Please wait.", color=0x4287f5, url=url)
        await interaction.response.send_message(embed=embed)
        start_time = time.perf_counter()
        try:
            download_audio(url, id)
        except:
            embed.title = "Error!"
            await interaction.edit_original_response(embed=embed)
            if os.path.exists(f"audio/{id}"):
                shutil.rmtree(f"audio/{id}")
            return

        end_time = time.perf_counter()
        embed.title = "Downloaded!"
        embed.description = f"Audio successfully downloaded under {round(end_time - start_time, 2)} s."
        await interaction.edit_original_response(embed=embed)
        await interaction.followup.send(f"{interaction.user.mention}. Here is your file.",file=discord.File(f"audio/{id}/download.mp3"))
        shutil.rmtree(f"audio/{id}")
        os.remove("audio/raw/temp.mp3")

    
    async def model_autocomplete(self,
        interaction: discord.Interaction,
        current: str,
    ) -> List[app_commands.Choice[str]]:
        choices = []
        for model in os.listdir("./assets/weights"):
            if model.endswith(".pth"):
                choices.append(model[:-4])
        return [
            app_commands.Choice(name=choice, value=choice)
            for choice in choices if current.lower() in choice.lower()
        ]
    
    @app_commands.command(name="sing", description="Make Character sing using AI!")
    @app_commands.autocomplete(model=model_autocomplete)
    async def sing(self, interaction: discord.Interaction, model: str, url: str, transpose: int = 0, protect: float = 0.33):
        embed = discord.Embed(title="Downloading audio...", description="Please wait.", color=0x4287f5, url=url)
        id = interaction.id
        path = os.getcwd()
        print(model)
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
            
            embed.title = f"Forcing {model} to sing..."
            await interaction.edit_original_response(embed=embed)
            try:
                self.voice_converter.change_sid(model+".pth")
                file_index1 = f'logs/{model}/added.index' 
                res = self.voice_converter.infer(vc_transform0=transpose, 
                                                 input_audio0=f"audio/{id}/vocal_{id}.wav.reformatted.wav_10.wav",
                                                 file_index1=file_index1,
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
