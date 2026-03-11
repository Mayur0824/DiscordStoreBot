import discord
from discord.ext import commands
import os

class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_channel_id = int(os.getenv("WELCOME_CHANNEL_ID", 0))

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not self.welcome_channel_id:
            print("Welcome channel ID not configured.")
            return
            
        channel = self.bot.get_channel(self.welcome_channel_id)
        if channel:
            embed = discord.Embed(
                title=f"Welcome to the Store, {member.name}! 🎉",
                description=f"Hello {member.mention}! Thanks for joining our community.\n\n"
                            "🛒 **Check out our products in <#shop>** (replace with real channel)\n"
                            "🎫 **Need help? Open a ticket in <#support>** (replace with real channel)\n\n"
                            "We hope you enjoy your stay!",
                color=discord.Color.brand_green()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"You are member #{member.guild.member_count}!")
            
            await channel.send(embed=embed)
        else:
            print(f"Could not find welcome channel with ID {self.welcome_channel_id}")

async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))
