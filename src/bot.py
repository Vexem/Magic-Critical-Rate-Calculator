import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# List of buffs with name, value, and type
buffs_options = {
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

def wit_bonus(wit):
    return 0.005 + 1.05**(wit - 20)

def base_magic_crit(wit):
    return wit_bonus(wit) * 5

def apply_buffs(base_rate, buffs):
    multiplicative = 1
    additive = 0
    for buff in buffs:
        if buff["type"] == "x":  
            multiplicative *= buff["value"]
        elif buff["type"] == "+":
            additive += buff["value"]
    return base_rate * multiplicative + additive

@bot.tree.command(name="help_magic_crit", description="Shows how to use the magic_crit command")
async def help_magic_crit(interaction: discord.Interaction):
    """Shows how to use the /help_magic_crit command"""
    buffs_list = "**📌 Available buffs (use the numbers separated by space):**\n"
    for key, value in buffs_options.items():
        buffs_list += f"`{key}`. {value['name']} ({value['type']}{value['value']})\n"
    
    help_text = (
        "**🔮 Usage of the `/magic_crit` command**\n"
        "📌 **Syntax:** `/magic_crit <WIT> <buff_numbers>`\n"
        "📌 **Example:** `/magic_crit 23 3 9` (Dance of Siren + Dark Squad)\n\n"
        f"{buffs_list}"
    )
    await interaction.response.send_message(help_text)

@bot.tree.command(name="magic_crit", description="Calculates the Magic Critical Rate")
async def magic_crit(interaction: discord.Interaction, wit: int, buff_numbers: str = ""):
    """Calculates the Magic Critical Rate percentage based on the WIT and selected buffs."""
    try:
        base_rate = base_magic_crit(wit)

        # Parsing the buff numbers (example: "3 9" for Dance of Siren + Dark Squad)
        buff_list = []
        if buff_numbers:
            selected_buffs = buff_numbers.split()
            for buff_num in selected_buffs:
                if buff_num in buffs_options:
                    buff_list.append(buffs_options[buff_num])
                else:
                    await interaction.response.send_message(f"⚠️ Buff number `{buff_num}` not recognized. Use `/help_magic_crit` to see the list.")
                    return

        # Apply the buffs
        rate = apply_buffs(base_rate, buff_list)
        final_rate = f"{rate:.2f}%" if rate <= 20 else f"20% ({rate:.2f}%)"

        # Show the applied buffs
        applied_buffs = "\n\t".join(f"`{buffs_options[num]['name']}`" for num in buff_numbers.split()) if buff_numbers else "No buffs"
        response = (
            f"**🔮 WIT:** `{wit}`\n"
            f"**✨ Applied buffs:** \n\t{applied_buffs}\n"
            f"**📊 Magic Critical Rate:** `{final_rate}`"
        )
        await interaction.response.send_message(response)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error in calculation: {str(e)}")

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'{bot.user} is online and slash commands are synchronized!')

bot.run(os.getenv("DISCORD_BOT_TOKEN"))