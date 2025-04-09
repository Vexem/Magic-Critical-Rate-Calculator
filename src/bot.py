import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from aiohttp import web  # Import aiohttp for the web server
import aiohttp
import asyncio

load_dotenv()

# Intents settings
intents = discord.Intents.default()
intents.message_content = True

# Initialize the bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Dictionary of available buffs
BUFFS_OPTIONS = {
    "1": {"name": "Wild Magic 2", "value": 2, "type": "+"},
    "2": {"name": "Prophecy of Water / PoF / CoV", "value": 2, "type": "+"},
    "3": {"name": "Necklace of Valakas", "value": 2, "type": "+"},
    "4": {"name": "Talisman: Wild Magic", "value": 2, "type": "+"},
    "5": {"name": "Active Augment: WM Level 10", "value": 4, "type": "+"},
    "6": {"name": "Passive Augment: WM (any)", "value": 4, "type": "+"},
    "7": {"name": "Infinity Scepter", "value": 1, "type": "+"},
    "8": {"name": "Dance of Siren", "value": 2, "type": "x"},
    "9": {"name": "Dark Squad lvl 3", "value": 1.01, "type": "x"},
    "10": {"name": "Magician's Will", "value": 1.05, "type": "x"}
}

# Calculation functions
def wit_bonus(wit: int) -> float:
    """Calculate the bonus based on WIT."""
    return 0.005 + 1.05 ** (wit - 20)

def base_magic_crit(wit: int) -> float:
    """Calculate the base Magic Critical Rate as a percentage."""
    return wit_bonus(wit) * 5

def apply_buffs(base_rate: float, buffs: list) -> float:
    """
    Apply buffs to the base rate.
    
    Buffs of type 'x' are multiplied,
    while buffs of type '+' are added.
    """
    multiplicative = 1
    additive = 0
    for buff in buffs:
        if buff["type"] == "x":
            multiplicative *= buff["value"]
        elif buff["type"] == "+":
            additive += buff["value"]
    return base_rate * multiplicative + additive

# Help command for magic_crit
@bot.tree.command(name="help_magic_crit", description="Show how to use the magic_crit command")
async def help_magic_crit(interaction: discord.Interaction):
    # Build the list of available buffs
    buffs_list = "**📌 Available Buffs (use numbers separated by space):**\n"
    for key, value in BUFFS_OPTIONS.items():
        buffs_list += f"`{key}`. {value['name']} ({value['type']}{value['value']})\n"

    help_text = (
        "**🔮 Usage of the `/magic_crit` command**\n"
        "1. **Syntax:** `/magic_crit <WIT> <buff_numbers>`\n"
        "2. **Example:** `/magic_crit 23 3 9` (uses Dance of Siren and Dark Squad)\n\n"
        f"{buffs_list}"
    )
    await interaction.response.send_message(help_text)

# Command to calculate the Magic Critical Rate
@bot.tree.command(name="magic_crit", description="Calculate the Magic Critical Rate")
async def magic_crit(interaction: discord.Interaction, wit: int, buff_numbers: str = ""):
    try:
        # Calculate the base rate
        base_rate = base_magic_crit(wit)

        # Parse the provided buff numbers
        buff_list = []
        if buff_numbers:
            selected_buffs = buff_numbers.split()
            for buff_num in selected_buffs:
                if buff_num in BUFFS_OPTIONS:
                    buff_list.append(BUFFS_OPTIONS[buff_num])
                else:
                    await interaction.response.send_message(
                        f"⚠️ Buff number `{buff_num}` not recognized. Use `/help_magic_crit` to see the list."
                    )
                    return

        # Apply buffs to the base rate
        rate = apply_buffs(base_rate, buff_list)
        final_rate = f"{rate:.2f}%" if rate <= 20 else f"20% (calculated: {rate:.2f}%)"

        # Prepare the list of applied buffs in a readable format
        applied_buffs = "\n\t".join(
            f"`{BUFFS_OPTIONS[num]['name']}`" for num in buff_numbers.split()
        ) if buff_numbers else "No buffs applied"

        response = (
            f"**🔮 WIT:** `{wit}`\n"
            f"**✨ Applied Buffs:**\n\t{applied_buffs}\n"
            f"**📊 Magic Critical Rate:** `{final_rate}`"
        )
        await interaction.response.send_message(response)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error calculating: {str(e)}")

# Minimal web server to satisfy Render's port requirement
async def handle(request):
    return web.Response(text="Discord Bot Running!")

async def start_webserver():
    port = int(os.getenv("PORT", 5000))
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    print(f"[WEB] Web server started on port {port}")
    await site.start()



# on_ready event: start both the bot and the web server
@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    try:
        synced = await bot.tree.sync()
        print(f"Synced slash commands: {len(synced)}")
    except Exception as e:
        print(f"Error syncing commands: {e}")

    # Start the web server in the background
    bot.loop.create_task(start_webserver())

if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    if token:
        print("Starting the bot...")
        bot.run(token)
    else:
        print("❌ Error: DISCORD_BOT_TOKEN not found in environment variables.")

async def auto_ping():
    """Periodically sends requests to the bot's service URL to keep it awake."""
    await bot.wait_until_ready()
    url = "https://magic-critical-rate-calculator.onrender.com"  # Replace with your actual service URL
    async with aiohttp.ClientSession() as session:
        while not bot.is_closed():
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        print(f"Auto-ping successful: {response.status}")
                    else:
                        print(f"Auto-ping failed: {response.status}")
            except Exception as e:
                print(f"Error during auto-ping: {e}")
            await asyncio.sleep(600)  # Waits 10 minutes before the next ping

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    try:
        synced = await bot.tree.sync()
        print(f"Synced slash commands: {len(synced)}")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    
    # Start the auto-ping task
    bot.loop.create_task(auto_ping())

