import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import os

TOKEN = "TOKEN"

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

music_queue = {}

yt_dl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ffmpeg_opts = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = youtube_dl.YoutubeDL(yt_dl_opts)

@bot.event
async def on_ready():
    print(f'{bot.user} is connected to the following server:\n')
    for server in bot.guilds:
        print(f'{server.name}(id: {server.id})')
    
    activity = discord.Game(name="admin:admin kad me pitas KO SAM")
    await bot.change_presence(status=discord.Status.do_not_disturb, activity=activity)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user.mention in message.content:
        await message.channel.send("bobanboban")
    
    await bot.process_commands(message)

    if 'bobanboban' in message.content:
        await message.add_reaction('👍')

async def play_next(ctx):
    guild_id = ctx.guild.id
    if guild_id in music_queue and len(music_queue[guild_id]) > 0:
        url = music_queue[guild_id].pop(0)
        await play_song(ctx, url)

async def play_song(ctx, url):
    guild_id = ctx.guild.id
    voice_channel = ctx.author.voice.channel

    if not voice_channel:
        await ctx.send("You need to be in a voice channel to play music.")
        return

    if ctx.voice_client is None:
        await voice_channel.connect()

    async with ctx.typing():
        try:
            info = ytdl.extract_info(url, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            url2 = info['url']
            source = await discord.FFmpegOpusAudio.from_probe(url2, **ffmpeg_opts)
            ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
            await ctx.send(f'Now playing: **{info["title"]}**')
        except Exception as e:
            await ctx.send(f"An error occurred while trying to play the song: {str(e)}")

@bot.command(name='play', help='To play a song')
async def play(ctx, url):
    guild_id = ctx.guild.id
    if guild_id not in music_queue:
        music_queue[guild_id] = []

    music_queue[guild_id].append(url)
    
    info = ytdl.extract_info(url, download=False)
    title = info.get('title', 'Unknown title')
    await ctx.send(f'Added to queue: **{title}**')
    
    if not ctx.voice_client or not ctx.voice_client.is_playing():
        await play_next(ctx)

@bot.command(name='skip', help='To skip the current song')
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await play_next(ctx)

@bot.command(name='disconnect', help='Disconnect the bot from the voice channel')
async def disconnect(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("The bot is not in a voice channel.")

@bot.command(name='queue', help='Shows the next 5 tracks in the queue')
async def queue(ctx):
    guild_id = ctx.guild.id
    if guild_id in music_queue and len(music_queue[guild_id]) > 0:
        queue_list = music_queue[guild_id][:5]
        message = "**🎵 Next 5 tracks in the queue:**\n\n"
        for i, url in enumerate(queue_list, start=1):
            try:
                info = ytdl.extract_info(url, download=False)
                title = info.get('title', 'Unknown title')
                message += f"{i}. **{title}**\n"
            except Exception as e:
                message += f"{i}. [Error retrieving title]\n"
        await ctx.send(message)
    else:
        await ctx.send("The queue is empty!")

bot.run(TOKEN)
