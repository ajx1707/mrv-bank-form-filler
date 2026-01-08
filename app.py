from flask import Flask, render_template, request, jsonify, redirect, url_for
import google.generativeai as genai
import os
from pathlib import Path
import tempfile
import time
import base64
import json
import re
import traceback
from openai import OpenAI
from groq import Groq
from form_prompts import get_system_prompt  # Import form-specific prompts
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure Flask app
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24).hex())

# API Keys from environment variables
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_API_KEY_2 = os.getenv('OPENROUTER_API_KEY_2')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_API_KEY_2 = os.getenv('GROQ_API_KEY_2')

# Validate API keys
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set!")
if not OPENROUTER_API_KEY:
    print("WARNING: Primary OPENROUTER_API_KEY not set!")

# Initialize OpenRouter clients (primary and backup)
openrouter_clients = []
if OPENROUTER_API_KEY:
    openrouter_clients.append(OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY
    ))
if OPENROUTER_API_KEY_2:
    openrouter_clients.append(OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY_2
    ))

# Initialize Groq clients (fallback)
groq_clients = []
if GROQ_API_KEY:
    groq_clients.append(Groq(api_key=GROQ_API_KEY))
if GROQ_API_KEY_2:
    groq_clients.append(Groq(api_key=GROQ_API_KEY_2))

# Store conversation history and collected form data per session
conversation_sessions = {}
form_data_sessions = {}

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/assistant')
def assistant():
    form_type = request.args.get('form', '')
    return render_template('assistant.html', form_type=form_type)

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/dd')
def dd_form():
    return render_template('dd.html')

@app.route('/tax_challan')
def tax_challan():
    return render_template('tax_challan.html')

@app.route('/account_opening')
def account_opening():
    return render_template('acc_new.html')

@app.route('/debit_card')
def debit_card():
    return render_template('debit.html')

@app.route('/loan_application')
def loan_application():
    return render_template('loan.html')

@app.route('/withdrawal')
def withdrawal():
    return render_template('withdrawl.html')

@app.route('/kyc')
def kyc():
    return render_template('Kyc.html')

@app.route('/account_closure')
def account_closure():
    return render_template('acc_close.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        
        # Configure Gemini with API key for audio transcription
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Read audio data directly
        audio_data = audio_file.read()
        
        try:
            # Create model for audio transcription
            model = genai.GenerativeModel('gemini-2.5-flash-lite')
            
            # Send audio data directly as base64
            response = model.generate_content([
                {
                    'mime_type': 'audio/webm',
                    'data': base64.b64encode(audio_data).decode('utf-8')
                },
                "Please transcribe this audio accurately. Only provide the transcription text without any additional commentary."
            ])
            
            transcription = response.text
            
            return jsonify({
                'success': True,
                'text': transcription
            })
            
        except Exception as e:
            raise e
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        form_type = data.get('form_type', '')  # Get pre-selected form type
        is_from_audio = data.get('is_from_audio', False)  # Check if input is from audio
        
        # Use Gemini for both audio and text (OpenRouter alternative)
        use_gemini = True  # Changed to always use Gemini
        
        # Debug logging
        print(f"DEBUG: form_type={form_type}, is_from_audio={is_from_audio}, use_gemini={use_gemini}")
        
        # Initialize conversation history for new sessions
        if session_id not in conversation_sessions:
            conversation_sessions[session_id] = []
            form_data_sessions[session_id] = {}
        
        # Get form-specific system prompt (much smaller than before!)
        system_prompt = get_system_prompt(form_type)
        
        # Add system prompt for first message
        if len(conversation_sessions[session_id]) == 0:
            conversation_sessions[session_id].append({
                'role': 'user',
                'parts': [system_prompt]
            })
            
            # If form type is pre-selected, inform the model
            if form_type:
                if form_type == 'deposit':
                    form_instruction = "The user has selected DEPOSIT SLIP. Start by greeting them and asking for the branch name."
                elif form_type == 'dd':
                    form_instruction = "The user has selected DEMAND DRAFT. Start by greeting them and asking for the branch name."
                elif form_type == 'tax_challan':
                    form_instruction = "The user has selected TAX CHALLAN ITNS-280. Start by greeting them and asking for their PAN number."
                elif form_type == 'account_opening':
                    form_instruction = """The user has selected ACCOUNT OPENING FORM for State Bank of India (Indian bank - INR currency, Indian citizenship assumed).
                    
                    IMPORTANT COLLECTION STRATEGY - ASK BY SECTIONS TO REDUCE API CALLS:
                    
                    1. START: Ask for branch, account type (Savings/Current/Salary), and debit card requirement together
                    2. PERSONAL DETAILS: "Let me get your personal details. Title (Mr/Mrs/Ms), full name (first, middle, last), date of birth (DD/MM/YYYY), and place of birth"
                    3. DOCUMENT SECTION: "For identity verification - which identity document type would you like to use (Aadhaar Card/Passport/Voter ID/Driving License)? Also provide your Aadhaar number (12 digits), PAN number (10 characters), the selected document's number, and expiry date if applicable"
                    4. CONTACT SECTION: "Your contact details: complete residential address, city, state (select from: Andhra Pradesh, Tamil Nadu, Karnataka, Kerala, Maharashtra, Gujarat, Rajasthan, Delhi, West Bengal, Uttar Pradesh, Other), PIN code (6 digits), mobile number (with +91), and email"
                    5. EMPLOYMENT SECTION: "Employment details: employer/company name, position/designation, monthly gross salary in rupees, and are you self-employed (yes/no)?"
                    6. ADDITIONAL INFO: "Additional information: marital status (single/married/divorced), number of dependents, purpose of account opening (you can select multiple: Salary Credit/Savings/Business Transactions/Investments/Others - if others, please specify), and card delivery preference (Collect from Branch/Home Delivery)"
                    
                    DEFAULT VALUES: Nationality = Indian (pre-filled, don't ask), Currency = INR (don't mention)
                    
                    Start by greeting and asking for branch, account type, and debit card requirement together."""
                elif form_type == 'debit_card':
                    form_instruction = """The user has selected DEBIT CARD APPLICATION for AXIS BANK (NRE Account holders with POA/LOA).
                    
                    COLLECTION STRATEGY - ASK BY SECTIONS:
                    
                    1. ACCOUNT DETAILS: "Let me help you with your debit card application. I need your NRE account number (up to 20 digits), customer ID, and the full name of the POA/LOA holder (Power of Attorney or Letter of Authority holder)"
                    2. PERSONAL INFO: "Now some personal details: mother's maiden name, date of birth, and the name you want printed on the card (max 18 characters, should not be a nickname)"
                    3. IMAGE CARD: "Would you like an image card? If yes, please provide the desired image code"
                    4. CARD TYPE: "Why are you applying? Is this for: New Card, Lost Card, Damaged Card, or Others? Also, is this a First or Joint application?"
                    5. OPTIONAL FIELDS: "If you have a Cross Self ID or BIN Number, please provide them. Otherwise we can skip these"
                    
                    IMPORTANT: DO NOT ask for Verifying Authority Details or Office Use section - those are filled by bank staff only.
                    
                    Start by greeting and asking for their NRE account number, customer ID, and POA/LOA holder name."""
                elif form_type == 'loan_application':
                    form_instruction = """The user has selected LOAN APPLICATION FORM for State Bank of India.
                    
                    COLLECTION STRATEGY - ASK QUESTIONS IN SMALL, EASY GROUPS:
                    
                    1. BASIC: "Account number and full name"
                    2. ADDRESS: "Complete home address with PIN code"
                    3. PREVIOUS ADDRESS: "Have you lived at your current address for less than 3 years? If yes, provide previous address. If no, we can skip this"
                    4. CONTACT: "Mobile number (with +91) and personal email. Do you also have a landline? (optional - can skip)"
                    5. DOB: "Date of birth (DD/MM/YYYY)"
                    6. MARITAL: "Marital status and number of dependents (excluding children)"
                    7. EMPLOYER: "Employer name and your designation/grade"
                    8. WORK LOCATION: "Employer's address and PIN code"
                    9. EMPLOYMENT: "Is your employment Temporary or Permanent? And how long have you been working there? (e.g., 5 years 3 months)"
                    10. WORK CONTACT: "Work email and work phone number (work phone is optional - can skip)"
                    11. LOAN BASICS: "How much loan amount do you need (in rupees) and what's the purpose? (Home/Vehicle/Personal/Education/Business/Other)"
                    12. REPAYMENT: "Repayment period in months and preferred method (Weekly/Fortnightly/Monthly)"
                    13. FINANCIAL 1: "Do you have any existing CSCJ loan? If yes, what's the repayment amount? If no, just say 0 or none"
                    14. FINANCIAL 2: "Shares amount and loan account amount (enter 0 if none for each)"
                    15. FINANCIAL 3: "Net loan amount and total monthly salary deduction"
                    
                    IMPORTANT RULES:
                    - Ask ONLY 1-3 related fields per question
                    - DO NOT list all remaining fields when user provides partial information
                    - Move to next question immediately after receiving current answer
                    - DO NOT ask for Office Use Only section
                    
                    Start by greeting and asking for account number and full name only."""
                elif form_type == 'withdrawal':
                    form_instruction = """The user has selected SAVINGS BANK WITHDRAWAL FORM for State Bank of India.
                    
                    COLLECTION STRATEGY - Simple and Quick:
                    
                    This is a simple form with only 7 fields. Ask in these groups:
                    
                    1. ACCOUNT INFO: "Branch name, account holder name (full name as per bank records), and account number (MUST be 14 digits)"
                    2. AMOUNT: "How much do you want to withdraw (in numbers)? Also provide the amount in words (e.g., Five Thousand Only)"
                    3. CONTACT: "Your phone or mobile number (10 digits)"
                    4. DATE: "Withdrawal date (DD/MM/YYYY) - or I can use today's date if you prefer"
                    
                    IMPORTANT: 
                    - Account number MUST be exactly 14 digits for withdrawal forms
                    - DO NOT ask for Office Use section - that's for bank staff.
                    
                    Start by greeting and asking for branch name, account holder name, and account number (14 digits) together."""
                elif form_type == 'kyc':
                    form_instruction = """The user has selected KYC UPDATE FORM for existing customers.
                    
                    COLLECTION STRATEGY - Simple and Conversational:
                    
                    This form updates KYC information with 12 fields. Ask in these groups:
                    
                    1. BASIC INFO: "Branch name (or I'll use Main Branch), your full name, and account number"
                    2. PERSONAL: "Date of birth (DD/MM/YYYY format)"
                    3. ADDRESS: "Complete address, village, post office, state, and PIN code (6 digits)"
                    4. FAMILY: "Father's or husband's name, and mother's name"
                    5. CONTACT: "Mobile number (10 digits)"
                    
                    IMPORTANT:
                    - If branch not mentioned, auto-fill with "Main Branch"
                    - Keep the conversation natural and friendly
                    - This is for updating existing customer records
                    
                    Start by greeting warmly and asking for customer name and account number."""
                elif form_type == 'account_closure':
                    form_instruction = """The user has selected ACCOUNT CLOSURE REQUEST FORM for IDFC First Bank.
                    
                    COLLECTION STRATEGY - Clear and Professional:
                    
                    This form closes an existing account with 11 fields. Ask in these groups:
                    
                    1. ACCOUNT INFO: "Customer ID (10 digits), account number to be closed (12 digits), and your full name"
                    2. PURPOSE: "What is the reason for closing this account?"
                    3. TRANSFER DETAILS: "Where should we transfer your remaining balance? I'll need:
                       - Beneficiary account number
                       - Account holder name
                       - Account type (savings or current)
                       - Bank name
                       - Branch name and city
                       - IFSC code (11 characters)"
                    4. DATE: "Date of request (DD/MM/YYYY) - or I can use today's date"
                    
                    IMPORTANT:
                    - Customer ID must be exactly 10 digits
                    - Account number must be exactly 12 digits
                    - IFSC code should be 11 characters
                    - Date auto-fills with today if not mentioned
                    
                    Start by greeting professionally and asking for customer ID, account number, and customer name."""
                else:
                    form_instruction = "Greet the user and ask which form they'd like to fill."
                
                conversation_sessions[session_id].append({
                    'role': 'model',
                    'parts': [f'Understood. {form_instruction}']
                })
            else:
                conversation_sessions[session_id].append({
                    'role': 'model',
                    'parts': ['Understood. I will help users with banking forms, collecting information one question at a time.']
                })
        
        # Add user message to history
        conversation_sessions[session_id].append({
            'role': 'user',
            'parts': [user_message]
        })
        
        # Generate response using OpenRouter (for text) or Gemini (for audio)
        if use_gemini:
            # Use Gemini for audio input
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-2.5-flash-lite')
            chat = model.start_chat(history=conversation_sessions[session_id][:-1])
            response = chat.send_message(user_message)
            response_text = response.text
        else:
            # Use OpenRouter with fallback to Groq for text input
            messages = []
            for msg in conversation_sessions[session_id]:
                if msg['role'] == 'user':
                    messages.append({"role": "user", "content": msg['parts'][0]})
                elif msg['role'] == 'model':
                    messages.append({"role": "assistant", "content": msg['parts'][0]})
            
            response_text = None
            last_error = None
            
            # Try OpenRouter clients (primary and backup)
            for i, client in enumerate(openrouter_clients, 1):
                try:
                    print(f"DEBUG: Attempting OpenRouter API call (key #{i})...")
                    response = client.chat.completions.create(
                        model="openai/gpt-oss-120b:free",
                        messages=messages,
                        extra_body={"reasoning": {"enabled": True}}
                    )
                    response_text = response.choices[0].message.content
                    print(f"DEBUG: OpenRouter key #{i} - Success!")
                    break
                except Exception as e:
                    last_error = str(e)
                    print(f"DEBUG: OpenRouter key #{i} failed: {last_error}")
                    continue
            
            # If all OpenRouter keys failed, try Groq as fallback
            if not response_text:
                print(f"DEBUG: All OpenRouter keys failed. Trying Groq fallback...")
                for i, groq_client in enumerate(groq_clients, 1):
                    try:
                        print(f"DEBUG: Attempting Groq API call (key #{i})...")
                        completion = groq_client.chat.completions.create(
                            model="openai/gpt-oss-120b",
                            messages=messages,
                            temperature=1,
                            max_completion_tokens=8192,
                            top_p=1,
                            stream=False
                        )
                        response_text = completion.choices[0].message.content
                        print(f"DEBUG: Groq key #{i} - Success!")
                        break
                    except Exception as e:
                        last_error = str(e)
                        print(f"DEBUG: Groq key #{i} failed: {last_error}")
                        continue
            
            # If all APIs failed, raise error
            if not response_text:
                raise Exception(f"All API keys failed. Last error: {last_error}")
        
        # Add assistant response to history
        conversation_sessions[session_id].append({
            'role': 'model',
            'parts': [response_text]
        })
        
        # Extract form data if present
        form_complete = False
        extracted_form_data = {}
        
        print(f"\n=== DEBUG: Response from AI ===")
        print(f"Response text: {response_text[:500]}...")  # First 500 chars
        print(f"Contains FORM_DATA: {'{FORM_DATA:' in response_text or 'FORM_DATA' in response_text}")
        
        if '{FORM_DATA:' in response_text or 'FORM_DATA' in response_text:
            form_complete = True
            
            # Try to find JSON data - handle both single and double curly braces
            # Pattern 1: {{FORM_DATA: {{...}}}} (double braces)
            match = re.search(r'\{\{FORM_DATA:\s*(\{\{.*?\}\})\}\}', response_text, re.DOTALL)
            if match:
                # Remove double braces from the JSON
                json_str = match.group(1).replace('{{', '{').replace('}}', '}')
            else:
                # Pattern 2: {FORM_DATA: {...}} (single braces)
                match = re.search(r'\{FORM_DATA:\s*(\{.*?\})\}', response_text, re.DOTALL)
                if match:
                    json_str = match.group(1)
                else:
                    # Pattern 3: JSON code block
                    match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                    if match:
                        json_str = match.group(1)
                    else:
                        # Pattern 4: Direct JSON with branch_name
                        match = re.search(r'(\{[^{}]*"branch_name"[^{}]*\})', response_text, re.DOTALL)
                        json_str = match.group(1) if match else None
            
            if match and json_str:
                try:
                    print(f"JSON string attempted: {json_str[:200]}...")
                    extracted_data = json.loads(json_str)
                    
                    # Process denomination breakdown if present
                    if 'denomination_breakdown' in extracted_data:
                        denom = extracted_data['denomination_breakdown']
                        for key, value in denom.items():
                            if key == 'coins':
                                extracted_data['denom_coins_qty'] = str(value)
                            else:
                                extracted_data[f'denom_{key}_qty'] = str(value)
                        del extracted_data['denomination_breakdown']
                    
                    # Ensure all denomination fields exist
                    for denom in ['2000', '500', '200', '100', '50', '20', '10', '5', 'coins']:
                        if f'denom_{denom}_qty' not in extracted_data:
                            extracted_data[f'denom_{denom}_qty'] = '0'
                    
                    form_data_sessions[session_id].update(extracted_data)
                    extracted_form_data = extracted_data
                    print(f"✓ Successfully extracted form data: {extracted_form_data}")
                    print(f"✓ Form type in data: {extracted_form_data.get('form_type', 'NOT FOUND')}")
                except Exception as e:
                    print(f"✗ Error parsing form data: {e}")
                    print(f"JSON string attempted: {json_str}")
                    form_complete = False
            else:
                print(f"✗ No JSON match found in response")
                form_complete = False
        
        # Clean response text
        clean_response = response_text
        if '{FORM_DATA:' in clean_response:
            clean_response = re.sub(r'\{FORM_DATA:.*?\}', '', clean_response, flags=re.DOTALL)
        clean_response = re.sub(r'```json.*?```', '', clean_response, flags=re.DOTALL)
        clean_response = clean_response.strip()
        
        print(f"\n=== RETURNING TO FRONTEND ===")
        print(f"form_complete: {form_complete}")
        print(f"form_data keys: {list(extracted_form_data.keys()) if extracted_form_data else 'EMPTY'}")
        
        return jsonify({
            'success': True,
            'response': clean_response,
            'session_id': session_id,
            'form_complete': form_complete,
            'form_data': extracted_form_data if form_complete else {}
        })
        
    except Exception as e:
        print(f"Error in chat: {e}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/get_form_data', methods=['POST'])
def get_form_data():
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        
        if session_id in form_data_sessions:
            return jsonify({
                'success': True,
                'form_data': form_data_sessions[session_id]
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No form data found for this session'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/reset_conversation', methods=['POST'])
def reset_conversation():
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        
        if session_id in conversation_sessions:
            del conversation_sessions[session_id]
        if session_id in form_data_sessions:
            del form_data_sessions[session_id]
        
        return jsonify({
            'success': True,
            'message': 'Conversation and form data reset successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Get port from environment variable (Render sets PORT automatically)
    port = int(os.getenv('PORT', 5000))
    
    # Use debug mode only in development
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
