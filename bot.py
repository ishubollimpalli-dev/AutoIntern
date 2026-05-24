import urllib.request
import json
import telebot # Ensure you have installed pyTelegramBotAPI

# Replace with your actual Telegram Bot Token from BotFather
BOT_TOKEN = "8343891625:AAFudC53VOB9vd516HE_6Hk2pqOz3h7RdmM"
bot = telebot.TeleBot(BOT_TOKEN)

def fetch_github_data(username):
    url = f"https://api.github.com/users/{username}"
    # Adding a User-Agent header is best practice for GitHub API
    req = urllib.request.Request(url, headers={'User-Agent': 'AutoIntern-Bot'})
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                
                # Extracting key data points
                name = data.get("name", username)
                repos = data.get("public_repos", 0)
                followers = data.get("followers", 0)
                bio = data.get("bio", "No bio available.")
                
                return f"🔍 **GitHub Analysis: {name}**\n\n📝 Bio: {bio}\n📁 Public Repos: {repos}\n👥 Followers: {followers}\n🔗 Link: https://github.com/{username}"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return f"❌ Error: GitHub user '{username}' not found."
        return f"❌ HTTP Error: {e.code}"
    except Exception as e:
        return f"❌ System Error: {str(e)}"

@bot.message_handler(commands=['analyse'])
def analyse_user(message):
    # Extract the username from the command (e.g., /analyse ishubollimpalli-dev)
    command_parts = message.text.split()
    
    if len(command_parts) < 2:
        bot.reply_to(message, "⚠️ Please provide a username. Format: /analyse <github_username>")
        return
        
    username = command_parts[1]
    bot.reply_to(message, f"⚙️ Fetching data for {username}...")
    
    # Call the urllib logic
    result = fetch_github_data(username)
    bot.reply_to(message, result)

print("🚀 AutoIntern Server is running. Waiting for commands...")
bot.infinity_polling()