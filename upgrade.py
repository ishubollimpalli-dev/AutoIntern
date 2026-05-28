import sqlite3

# Connect to your local database
conn = sqlite3.connect('autointern.db')
cursor = conn.cursor()

# Upgrade ALL current users in the database to Premium (which is just you right now)
cursor.execute("UPDATE users SET is_premium = 1")
conn.commit()
conn.close()

print("🎉 Admin Override Successful: Your account is now Premium!")