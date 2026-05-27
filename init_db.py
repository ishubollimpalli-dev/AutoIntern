import sqlite3

def setup_database():
    # Connects to database file (creates it if it doesn't exist)
    conn = sqlite3.connect('autointern.db')
    cursor = conn.cursor()
    
    # Create the users table for tracking premium status
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        resume_count INTEGER DEFAULT 0,
        is_premium BOOLEAN DEFAULT FALSE
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Database 'autointern.db' initialized with 'users' table successfully.")

if __name__ == "__main__":
    setup_database()