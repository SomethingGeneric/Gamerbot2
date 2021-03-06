import discord
from discord.ext import commands

from util_functions import *
from global_config import configboi


# Hopefully we'll never need logging here


class Debug(commands.Cog):
    """Stuff that the developer couldn't find a better category for"""

    def __init__(self, bot):
        self.bot = bot
        self.confmgr = configboi("config.txt", False)

    @commands.command()
    async def checkcog(self, ctx, *, n):
        """check if cog is a thing"""
        try:
            if ctx.bot.get_cog(n) is not None:
                await ctx.send(
                    embed=infmsg("Debug Tools", "Bot was able to find `" + n + "`")
                )
            else:
                await ctx.send(
                    embed=errmsg("Debug Tools", "Bot was not able to find `" + n + "`")
                )
        except Exception as e:
            await ctx.send(
                embed=errmsg(
                    "Debug Tools - ERROR",
                    "Had error `" + str(e) + "` while checking cog `" + n + "`",
                )
            )

    @commands.command()
    async def gitstatus(self, ctx):
        """Show the output of git status"""
        commit_msg = await run_command_shell(
            "git --no-pager log --decorate=short --pretty=oneline -n1"
        )
        await ctx.send(embed=infmsg("Git Status", "```" + commit_msg + "```"))

    @commands.command()
    async def purgesyslog(self, ctx):
        """Delete all existing syslogs (USE WITH CARE) (Owner only)"""
        if ctx.message.author.id == self.bot.owner_id:
            purged = await run_command_shell("rm system_log* -v")
            await ctx.send(
                embed=infmsg("Syslog Purger", "We purged:\n```" + purged + "```")
            )
        else:
            await ctx.send(embed=errmsg("Oops", wrongperms("purgesyslog")))


def setup(bot):
    bot.add_cog(Debug(bot))
