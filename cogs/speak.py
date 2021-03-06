# System
import os, random

# Pip
import discord
from discord.ext import commands, tasks
import asyncio

# Mine
from channel_state import VoiceState
from util_functions import *


class Speak(commands.Cog):
    """Text to speech go brr"""

    def __init__(self, bot):
        self.vs = VoiceState()

        self.bot = bot
        self.voice_client = None
        self.audiosrc = None
        self.isDone = False

        self.troll_task.start()

        self.chat_channels = []

        if os.path.exists(".chatchannels"):
            with open(".chatchannels") as f:
                channels = f.read().strip().split("\n")
            for chan in channels:
                self.chat_channels.append(int(chan))

        syslog.log("Speak-Client", "Instance created and setup")

    def cog_unload(self):
        self.troll_task.cancel()

    def setDone(self):
        self.isDone = True

    @commands.command()
    async def makechatchannel(self, ctx):
        adm = False
        for role in ctx.message.author.roles:
            if role.name == "gb_mod":
                adm = True

        if adm:
            self.chat_channels.append(ctx.message.channel.id)
            with open(".chatchannels", "a+") as f:
                f.write(str(ctx.message.channel.id) + "\n")
            await ctx.send("Done!")
        else:
            await ctx.send("You're not a mod")

    async def speakInChannel(self, ctx, text="", chan=None, stealth=False, file=None):
        if self.voice_client is None and not self.vs.check_state():
            syslog.log(
                "Speak-Client",
                "This cog was not playing, nor were others. It's go time.",
            )

            try:

                if ctx is not None and ctx.author.voice is not None:
                    channel = ctx.author.voice.channel
                else:
                    channel = chan

                if channel is not None:
                    syslog.log(
                        "Speak-Client",
                        "The author is in a channel, so we're attempting to join them.",
                    )
                    if file == None:
                        await run_command_shell(
                            'espeak-ng -w espeak.wav "' + text + '"'
                        )
                        syslog.log(
                            "Speak-Client",
                            "We have the TTS audio file ready. Playing it.",
                        )
                    else:
                        syslog.log("Speak-Client", "We're using a file")
                    self.voice_client = await channel.connect()
                    self.vs.set_state("1")
                    syslog.log("Speak-Client", "We're in voice now.")
                    fn = "espeak.wav"
                    if file != None:
                        fn = file
                    self.audiosrc = discord.FFmpegPCMAudio(fn)
                    self.isDone = False
                    self.voice_client.play(
                        self.audiosrc,
                        after=lambda e: print("Player error: %s" % e)
                        if e
                        else self.setDone(),
                    )
                    while self.voice_client.is_playing():
                        self.isDone = False
                        if self.isDone == True:
                            break
                        await asyncio.sleep(1)
                    syslog.log("Speak-Client", "We're done playing. Cleaning up.")

                    await self.voice_client.disconnect()
                    self.voice_client = None
                    self.audiosrc = None
                    self.isDone = True
                    await run_command_shell("rm espeak.wav")
                    self.vs.set_state("0")
                    syslog.log("Speak-Client", "We're done cleaning up. All done!")
                    if stealth:
                        return True
                else:
                    if not stealth:
                        await ctx.send(
                            embed=errmsg(
                                "Spoken Word", "You're not in a voice channel."
                            )
                        )
                    else:
                        return False
            except Exception as e:
                syslog.log("Speak-Client-Important", "Error: " + str(e))
                await ctx.send(embed=errmsg("Spoken Word", "`" + str(e) + "`"))

        else:
            await ctx.send(
                embed=errmsg(
                    "Spoken Word", "I'm already in a voice channel, and busy."
                ),
                reference=ctx.message,
            )
            syslog.log("Speak-Client", "VC is busy somewhere. Doing nothing.")

    @commands.command()
    async def tts(self, ctx, *, thing, stealth=False):
        """Talk in voice channel"""
        syslog.log(
            "Speak-Client", "Calling speakInChannel for " + ctx.author.display_name
        )
        await self.speakInChannel(
            ctx, ctx.author.display_name + " says " + thing, None, False
        )

    async def do_meow(self, ctx=None, chan=None):
        files = os.listdir("sounds")
        fn = "sounds/" + random.choice(files)
        syslog.log("Meow-Client", "Playing: " + fn)
        await self.speakInChannel(ctx=ctx, chan=chan, file=fn)

    @commands.command()
    async def meow(self, ctx):
        """I am a cat :)"""
        await self.do_meow(ctx)

    @commands.Cog.listener()
    async def on_message(self, message):
        if " bee " in message.content.lower() or " bees " in message.content.lower():
            syslog.log("Speak-Memes", "BEE MOVIE ALERT!!")
            with open("data/bee.txt") as f:
                quote = random.choice(f.read().split("\n"))
                if message.author.voice is not None:
                    ctx = await self.bot.get_context(message)
                    syslog.log("Speak-Client", "Initializing meme session")
                    tried = await self.speakInChannel(ctx, quote, None, True)
                    if tried:
                        syslog.log(
                            "Speak-Memes", "SPOKE BEE MOVIE QUOTE IN VOICE CHANNEL!!"
                        )
                    else:
                        syslog.log(
                            "Speak-Client",
                            "Falling back to text since voice is too busy for memes.",
                        )
                        await message.channel.send("`" + quote + "`")
                        syslog.log("Speak-Memes", "SENT BEE MOVIE QUOTE IN TEXT CHAT")
                else:
                    syslog.log(
                        "Speak-Client",
                        "Falling back to text since voice is too busy for memes. (Voice not attempted)",
                    )
                    await message.channel.send("`" + quote + "`")
                    syslog.log("Speak-Memes", "SENT BEE MOVIE QUOTE IN TEXT CHAT")

        if (
            message.channel.id in self.chat_channels
            and message.author != self.bot.user
            and message.content != "-makechatchannel"
            or "hey chatterbot" in message.content
        ):
            resp = await run_command_shell(
                'python3 bin/thechatbot.py "'
                + message.content.replace("\"", '\'').replace("hey chatterbot", "")
                + '"'
            )

            if len(resp) < 1024:
                await message.channel.send(resp, reference=message)
            else:
                url = paste("<h1><code>" + resp + "</code></h1>")
                await message.channel.send(url, reference=message)
            if message.author.voice is not None:
                ctx = await self.bot.get_context(message)
                syslog.log("Speak-Client", "Speaking response as well")
                await self.speakInChannel(ctx=ctx, text=resp)

    @tasks.loop(seconds=120)
    async def troll_task(self):
        for guild in self.bot.guilds:
            for vc in guild.voice_channels:
                if len(vc.members) != 0:
                    fail = False
                    for member in vc.members:
                        if str(member.id) in DONT_SCARE:
                            fail = True
                    if random.randint(1, 10) == 5:
                        if not fail:
                            if random.randint(1, 3) == 2:
                                await self.speakInChannel(
                                    None,
                                    text="Hi folks of "
                                    + str(guild.name)
                                    + random.choice(IMAGE_RESPONSES),
                                    chan=vc,
                                    stealth=True,
                                )
                            else:
                                await self.do_meow(chan=vc)

    @troll_task.before_loop
    async def before_the_troll_task(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Speak(bot))
