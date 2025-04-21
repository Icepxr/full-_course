import discord
import os
import json
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import google.generativeai as genai

# โหลด ENV
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('api')
GUILD_ID =  os.getenv('GUILD_ID') # ใส่ Server ID ของคุณ

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# ---------------- CONFIG ----------------
generation_config = {
    "temperature": 0.8,
    "max_output_tokens": 512,
    "top_p": 1
}

HISTORY_FILE = r"S:\L1_Webdev\full_course\full-_course\botdiscord\chat_history.json"
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

def split_message(text, limit=4000):
    return [text[i:i+limit] for i in range(0, len(text), limit)]

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

chat_history = load_history()

# ---------------- SLASH COMMANDS ----------------

@app_commands.command(name="ask", description="ถามคำถามกับ SAKURA\U0001f338")
async def ask(interaction: discord.Interaction, prompt: str):
    user_id = str(interaction.user.id)
    await interaction.response.defer()

    if user_id not in chat_history:
        chat_history[user_id] = []

    chat_history[user_id].append({"role": "user", "parts": prompt})
    chat = model.start_chat(history=chat_history[user_id])

    try:
        response = chat.send_message(prompt, generation_config=generation_config)
        chat_history[user_id].append({"role": "model", "parts": response.text})
        save_history(chat_history)

        for i, part in enumerate(split_message(response.text)):
            embed = discord.Embed(
                title=f"{'(ต่อ)' if i > 0 else ''}",
                description=part,
                color=discord.Color.purple()
            )
            await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(
            title="SAKURA\U0001f338 \u274c Error",
            description=str(e),
            color=discord.Color.red()
        ))

@app_commands.command(name="reset", description="ล้างประวัติการสนทนากับ SAKURA\U0001f338")
async def reset(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if user_id in chat_history:
        del chat_history[user_id]
        save_history(chat_history)
        await interaction.response.send_message("\U0001f9f9 ล้างประวัติเรียบร้อยแล้วค่ะ", ephemeral=True)
    else:
        await interaction.response.send_message("ไม่พบประวัติของคุณค่ะ~", ephemeral=True)

@app_commands.command(name="history", description="ดูบทสนทนาเก่ากับ SAKURA\U0001f338")
async def history(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    history = chat_history.get(user_id, [])
    await interaction.response.defer()

    if not history:
        await interaction.followup.send("\U0001f4ed ไม่มีบทสนทนาในระบบค่ะ")
        return

    summary = ""
    for turn in history[-10:]:
        role = "\U0001f464 คุณ:" if turn["role"] == "user" else "\U0001f338 SAKURA:"
        content = turn["parts"]
        summary += f"**{role}** {content}\n\n"

    for part in split_message(summary):
        embed = discord.Embed(
            title="\U0001f4dc ประวัติการสนทนา",
            description=part,
            color=discord.Color.teal()
        )
        await interaction.followup.send(embed=embed)

@app_commands.command(name="help", description="ดูวิธีใช้งาน SAKURA\U0001f338")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="\U0001f4da วิธีการใช้งาน SAKURA\U0001f338",
        description="""
        **คำสั่งที่ใช้ได้:**
        - `/ask <คำถาม>`: ถามคำถามกับ SAKURA🌸
        - `/reset`: ล้างประวัติการสนทนา
        - `/history`: ดูบทสนทนาเก่า
        - `/sleep`: ปิดบอท (เฉพาะแอดมิน)
        - `/reload`: โหลดคำสั่งใหม่ (เฉพาะแอดมิน)
        - `/ping`: เช็กว่าบอทยังทำงานอยู่มั้ย
        
        """,
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@app_commands.command(name="sleep", description="ให้ SAKURA\U0001f338 เข้านอน (เฉพาะแอดมิน)")
@app_commands.checks.has_permissions(administrator=True)
async def sleep(interaction: discord.Interaction):
    await interaction.response.send_message("\U0001f4a4 SAKURA\U0001f338 เข้านอนแล้วค่ะ", ephemeral=True)
    await bot.close()

        
@app_commands.command(name="ling", description="เช็กว่าบอทยังทำงานอยู่มั้ย")
async def ling(interaction: discord.Interaction):
    await interaction.response.send_message("LONGG!")



@app_commands.command(name="reload", description="โหลดคำสั่งใหม่ (เฉพาะแอดมิน)")
@discord.app_commands.checks.has_permissions(administrator=True)
async def reload(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        guild = discord.Object(id=GUILD_ID)
        bot.tree.clear_commands(guild=guild)
        all_commands(guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"🔁 Reloaded {len(synced)} commands")
        await interaction.followup.send(
            f"🔁 Reloaded {len(synced)} commands สำเร็จแล้ว", ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(
            f"❌ เกิดข้อผิดพลาด: {e}", ephemeral=True
        )
# ---------------- STARTUP ----------------

def  all_commands( guild):
        bot.tree.add_command(ask, guild=guild)
        bot.tree.add_command(reset, guild=guild)
        bot.tree.add_command(history, guild=guild)
        bot.tree.add_command(help_command, guild=guild)
        bot.tree.add_command(sleep, guild=guild)
        bot.tree.add_command(reload, guild=guild)
        bot.tree.add_command(ling, guild=guild)

@bot.event
async def on_ready():
    try:
        # ✅ 1. เคลียร์คำสั่ง Global (ทั่วโลก)
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync(guild=None)  # sync เพื่อให้ global ว่างจริง

        # ✅ 2. เตรียม Guild Object
        guild = discord.Object(id=GUILD_ID)

        # ✅ 3. เคลียร์คำสั่งใน guild เฉพาะ
        bot.tree.clear_commands(guild=guild)

        # ✅ 4. เพิ่มคำสั่งใหม่
        all_commands(guild)
        # bot.tree.add_command(ask, guild=guild)
        # bot.tree.add_command(reset, guild=guild)
        # bot.tree.add_command(history, guild=guild)
        # bot.tree.add_command(help_command, guild=guild)
        # bot.tree.add_command(sleep, guild=guild)
        # bot.tree.add_command(reload, guild=guild)
        # bot.tree.add_command(ping, guild=guild)

        # ✅ 5. Sync คำสั่งเฉพาะใน guild
        synced = await bot.tree.sync(guild=guild)
        print(f"✅ Synced {len(synced)} commands to guild {GUILD_ID}")
        print(f"🟢 Logged in as {bot.user}")


    except Exception as e:
        print(f"❌ Error syncing commands: {e}")


bot.run(DISCORD_TOKEN)
