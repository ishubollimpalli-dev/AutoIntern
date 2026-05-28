import os
import logging
import sqlite3
import pypdf
import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

# 1. Load the environment variables from your .env file
load_dotenv()

# Setup basic logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- DATABASE HELPER FUNCTIONS ---
def get_user_data(user_id):
    conn = sqlite3.connect('autointern.db')
    cursor = conn.cursor()
    cursor.execute("SELECT resume_count, is_premium FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if not row:
        # If user is new, insert them into database automatically
        cursor.execute("INSERT INTO users (user_id, resume_count, is_premium) VALUES (?, 0, 0)", (user_id,))
        conn.commit()
        row = (0, 0)
        
    conn.close()
    return {"resume_count": row[0], "is_premium": bool(row[1])}

def increment_user_count(user_id):
    conn = sqlite3.connect('autointern.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET resume_count = resume_count + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# --- PDF PARSING HELPER ---
def extract_text_from_pdf(file_path):
    try:
        with open(file_path, 'rb') as file:
            reader = pypdf.PdfReader(file)
            first_page = reader.pages[0]
            return first_page.extract_text()
    except Exception as e:
        return f"Parsing Error: {str(e)}"

# --- LOCAL OLLAMA AI HELPER ---
def query_local_llm(prompt_text):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "phi3", 
        "prompt": prompt_text,
        "stream": False
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get("response", "Error: AI generation failed.")
    except Exception as e:
        return f"Backend Error: Ensure Ollama is running locally. Details: {str(e)}"

# --- MAIN DOCUMENT DOWNLOAD & ANALYSIS HANDLER ---
async def handle_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_profile = get_user_data(user_id)
    
    # --- REVENUE GATE (PAYMENT BUTTON) ---
    if not user_profile["is_premium"] and user_profile["resume_count"] >= 1:
        keyboard = [
            [InlineKeyboardButton("Unlock Premium (₹149)", url="https://example.com/payment-placeholder")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚠️ Free tier limit reached (1/1).\n\n"
            "Please upgrade to Premium for ₹149 to unlock unlimited AI ATS scans and formatting feedback.",
            reply_markup=reply_markup
        )
        return

    if update.message.document.mime_type != 'application/pdf':
        await update.message.reply_text("❌ Error: Please upload a valid PDF document.")
        return

    processing_msg = await update.message.reply_text("📥 Analyzing resume... This may take a few seconds.")

    # Download the file
    tg_file = await update.message.document.get_file()
    
    # Ensure the downloads directory exists
    os.makedirs('downloads', exist_ok=True)
    saved_file_path = f"downloads/{user_id}_resume.pdf"
    await tg_file.download_to_drive(saved_file_path)

    # Extract text
    extracted_text = extract_text_from_pdf(saved_file_path)
    
    # --- EDGE CASE HANDLING (SCANNED PDFS) ---
    if not extracted_text or len(extracted_text.strip()) < 50:
        await processing_msg.edit_text(
            "❌ Error: Cannot read text from this document. It appears to be an image-based or scanned PDF. "
            "Please upload a standard text-based PDF."
        )
        return
    
    system_prompt = (
        "You are an elite ATS (Applicant Tracking System) Analyzer.\n"
        "Analyze the raw resume text provided below and strictly return your findings inside this layout structure:\n\n"
        "1. ATS Score: (Out of 100)\n"
        "2. Missing Keywords: (List 3 critical skills missing based on standard tech roles)\n"
        "3. Formatting Red Flags: (Identify spacing or layout extraction issues)\n"
        "4. Final Verdict: (One sentence defining candidate job readiness)\n\n"
        f"Candidate Resume Text:\n{extracted_text}"
    )

    increment_user_count(user_id)
    
    # --- EXECUTE THE LLM ---
    ai_analysis = query_local_llm(system_prompt)
    
    # Send result to user
    await processing_msg.edit_text(ai_analysis)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to AutoIntern. Upload your resume PDF directly to run a full ATS analysis.")

# --- INITIALIZATION ENGINE ---
def main():
    # Safely read the token from the hidden .env file
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not BOT_TOKEN:
        print("CRITICAL ERROR: TELEGRAM_BOT_TOKEN not found in .env file.")
        return

    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handle the basic entry command
    application.add_handler(CommandHandler("start", start_command))
    
    # Handle document submissions (Strictly PDF format)
    application.add_handler(MessageHandler(filters.Document.PDF, handle_resume))
    
    print("AutoIntern System Online. Polling for users...")
    application.run_polling()

if __name__ == '__main__':
    main()