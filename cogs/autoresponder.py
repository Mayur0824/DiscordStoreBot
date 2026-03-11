import discord
from discord.ext import commands
from discord import app_commands
from database import db_handler

class AutoresponderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Cache triggers to avoid hitting the DB on every single message
        self.triggers = []

    async def cog_load(self):
        # Load triggers into memory on startup
        self.triggers = await db_handler.get_all_autoresponders()

    @app_commands.command(name="ar-add", description="Admin only: Add an autoresponder trigger")
    @app_commands.describe(
        trigger="The word or phrase to trigger on",
        text="The text response (optional)",
        image="The image response (optional)"
    )
    @app_commands.default_permissions(administrator=True)
    async def ar_add(self, interaction: discord.Interaction, trigger: str, text: str | None = None, image: discord.Attachment | None = None):
        if not text and not image:
            await interaction.response.send_message("You must provide either text or an image for the response.", ephemeral=True)
            return

        trigger_lower = trigger.lower()
        image_url = image.url if image else None

        try:
            await db_handler.add_autoresponder(trigger_lower, text, image_url)
            if trigger_lower not in self.triggers:
                self.triggers.append(trigger_lower)
            await interaction.response.send_message(f"✅ Autoresponder added for trigger: `{trigger_lower}`", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to save autoresponder: {e}", ephemeral=True)

    @app_commands.command(name="ar-remove", description="Admin only: Remove an autoresponder")
    @app_commands.describe(trigger="The trigger word to remove")
    @app_commands.default_permissions(administrator=True)
    async def ar_remove(self, interaction: discord.Interaction, trigger: str):
        trigger_lower = trigger.lower()
        if trigger_lower not in self.triggers:
            await interaction.response.send_message(f"⚠️ No autoresponder found for `{trigger_lower}`.", ephemeral=True)
            return

        try:
            await db_handler.delete_autoresponder(trigger_lower)
            self.triggers.remove(trigger_lower)
            await interaction.response.send_message(f"✅ Autoresponder removed for trigger: `{trigger_lower}`", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to delete autoresponder: {e}", ephemeral=True)

    @app_commands.command(name="ar-list", description="Admin only: List all autoresponders")
    @app_commands.default_permissions(administrator=True)
    async def ar_list(self, interaction: discord.Interaction):
        if not self.triggers:
            await interaction.response.send_message("No autoresponders are currently set up.", ephemeral=True)
            return
            
        formatted_list = ", ".join([f"`{t}`" for t in self.triggers])
        embed = discord.Embed(title="Autoresponder Triggers", description=formatted_list, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # Check if the message contains any of the cached triggers
        content_lower = message.content.lower()
        
        # We sort triggers by length descending so longer phrases match before single words
        # (e.g. "how to buy" matches before "buy")
        sorted_triggers = sorted(self.triggers, key=len, reverse=True)
        
        for trigger in sorted_triggers:
            if trigger in content_lower:
                data = await db_handler.get_autoresponder(trigger)
                if data:
                    response_text, image_url = data
                    
                    # Send response
                    if image_url and response_text:
                        await message.channel.send(content=response_text)
                        await message.channel.send(content=image_url)
                    elif image_url:
                        await message.channel.send(content=image_url)
                    elif response_text:
                        await message.channel.send(content=response_text)
                        
                    # Stop checking after the first successful trigger to avoid spam
                    break

async def setup(bot):
    await bot.add_cog(AutoresponderCog(bot))
