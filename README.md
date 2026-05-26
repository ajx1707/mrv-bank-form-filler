# 🏦 Banking Form Assistant

An AI-powered voice and text assistant for filling out banking forms, designed especially for elderly users and those who are not tech-savvy.
## 🔗Live Demo
https://mrv-bank-form-filler-1.onrender.com
## ✨ Features

- **Voice Input**: Speak naturally to fill forms using audio transcription
- **Text Input**: Type responses if preferred
- **Multiple Form Types**: Supports 10 different banking forms
- **Smart Assistance**: Auto-fills dates, validates data, converts amounts to words
- **Elderly-Friendly**: Patient, clear instructions and simple interface

## 📋 Supported Forms

1. **Deposit Slip** - Cash/Cheque deposits
2. **Demand Draft** - DD/Banker's Cheque applications
3. **Tax Challan** - ITNS-280 tax payments
4. **Account Opening** - New account applications
5. **Debit Card** - Debit card requests
6. **Loan Application** - Personal/home/business loans
7. **Withdrawal** - Savings bank withdrawals
8. **KYC Update** - Know Your Customer information
9. **Account Closure** - Close existing accounts

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd intern
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   - The `.env` file should already exist with your API keys
   - If not, copy from example:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and add your API keys

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open in browser**
   ```
   http://localhost:5000
   ```

## 🌐 Deploy to Render

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

### Quick Deploy Steps:

1. Push code to GitHub
2. Connect GitHub repo to Render
3. Add environment variables in Render dashboard
4. Deploy!

## 🔑 API Keys Required

### Gemini API (for voice transcription):
- Get from: https://makersuite.google.com/app/apikey
- Free tier available

### OpenRouter API (for chat):
- Get from: https://openrouter.ai/keys
- Free models available

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **AI Models**: 
  - Google Gemini 2.5 Flash Lite (audio transcription)
  - OpenAI GPT via OpenRouter (text chat)
- **Frontend**: HTML, JavaScript, CSS
- **Hosting**: Render (free tier)

## 📁 Project Structure

```
intern/
├── app.py                 # Main Flask application
├── form_prompts.py        # Form-specific AI prompts
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (local)
├── .env.example          # Environment template
├── .gitignore            # Git ignore rules
├── render.yaml           # Render deployment config
├── DEPLOYMENT.md         # Deployment guide
├── static/               # Static assets (images)
├── templates/            # HTML templates
│   ├── home.html         # Landing page
│   ├── assistant.html    # AI chat interface
│   ├── form.html         # Form selector
│   └── [various form templates]
└── __pycache__/          # Python cache (ignored)
```

## 🔒 Security

- ✅ API keys stored in environment variables
- ✅ `.env` file in `.gitignore` (never committed)
- ✅ Production mode disables debug
- ✅ Secret key for Flask sessions

## 🐛 Troubleshooting

### App won't start locally?
- Check Python version (3.8+)
- Verify all dependencies installed: `pip install -r requirements.txt`
- Confirm `.env` file exists with valid API keys

### API errors?
- Check API keys are correct in `.env`
- Verify API quotas not exceeded
- Check internet connection

### Forms not generating?
- Check browser console for errors
- Verify API responses in network tab
- Check Render logs if deployed

## 📝 Development Notes

### Adding a New Form:

1. Create HTML template in `templates/`
2. Add route in `app.py`
3. Add form prompt function in `form_prompts.py`
4. Update `get_system_prompt()` function
5. Add form link to `home.html` or `form.html`

### Testing Locally:

```bash
# Test transcription endpoint
curl -X POST -F "audio=@test.webm" http://localhost:5000/transcribe

# Test chat endpoint
curl -X POST -H "Content-Type: application/json" \
  -d '{"message":"Hello","session_id":"test"}' \
  http://localhost:5000/chat
```

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home page |
| `/assistant` | GET | AI chat interface |
| `/form` | GET | Form selector |
| `/transcribe` | POST | Audio transcription |
| `/chat` | POST | Process user message |
| `/get_form_data` | POST | Retrieve collected data |
| `/reset_conversation` | POST | Clear session |



---

**Security Warning**: Never commit `.env` file or share API keys publicly!
