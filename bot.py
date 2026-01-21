import discord
from discord.ext import commands
import requests
import tempfile
import re
import asyncio

TOKEN = "トークン"

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

voice_client = None
text_channel = None

# VOICEVOX
def post_audio_query(text, speaker):
    return requests.post(
        "http://127.0.0.1:50021/audio_query",
        params={"text": text, "speaker": speaker}
    ).json()

def post_synthesis(query, speaker):
    return requests.post(
        "http://127.0.0.1:50021/synthesis",
        json=query,
        params={"speaker": speaker}
    ).content

def save_tempfile(text, speaker):
    q = post_audio_query(text, speaker)
    audio = post_synthesis(q, speaker)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio)
        return f.name

def clean_text(text):
    return re.sub(r'https?://\S+|www\.\S+', 'URL', text)

# 起動
@bot.event
async def on_ready():
    print(" 起動完了")

# 読み上げ
@bot.event
async def on_message(message):
    global voice_client

    if message.author.bot:
        return

    await bot.process_commands(message)

    if message.channel != text_channel:
        return

    if not voice_client or voice_client.is_playing():
        return

    path = save_tempfile(clean_text(message.content), 1)
    voice_client.play(discord.FFmpegPCMAudio(path))

# /join
@bot.slash_command(name="join", description="VCに参加")
async def join(ctx):
    global voice_client, text_channel

    await ctx.respond("接続中...")

    if not ctx.author.voice:
        await ctx.edit(content="VCに入ってから呼んでね")
        return

    text_channel = ctx.channel

    async def connect_vc():
        global voice_client

        if ctx.guild.voice_client:
            await ctx.guild.voice_client.disconnect()

        voice_client = await ctx.author.voice.channel.connect()
        await ctx.edit(content="接続したよ！")

    asyncio.create_task(connect_vc())

# /leave
@bot.slash_command(name="leave", description="VCから退出")
async def leave(ctx):
    global voice_client, text_channel

    await ctx.respond("切断中...")

    if voice_client:
        await voice_client.disconnect()
        voice_client = None
        text_channel = None

    await ctx.edit(content="切断したよ！")

bot.run(TOKEN)