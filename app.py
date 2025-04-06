import os
import base64
import json
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import functions from existing modules
from brain_of_the_doctor import encode_image, generate_doctor_response_text, analyze_image_with_query
from voice_of_the_patient import record_audio, transcribe_with_groq
from voice_of_the_doctor import text_to_speech_with_elevenlabs

app = Flask(__name__, static_url_path='/static', static_folder='static')
CORS(app)  # Enable CORS for all routes

# Constants
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

# Fallback warning for missing API keys
if not GROQ_API_KEY:
    print("Warning: GROQ_API_KEY not found in environment variables. Please set it for production use.")
    
if not ELEVENLABS_API_KEY:
    print("Warning: ELEVENLABS_API_KEY not found in environment variables. Please set it for production use.")

MULTIMODAL_PROMPT = """You have to act as a professional doctor, i know you are not but this is for learning purpose. 
            What's in this image?. Do you find anything wrong with it medically? 
            If you make a differential, suggest some remedies for them. Donot add any numbers or special characters in 
            your response. Your response should be in one long paragraph. Also always answer as if you are answering to a real person.
            Donot say 'In the image I see' but say 'With what I see, I think you have ....'
            Dont respond as an AI model in markdown, your answer should mimic that of an actual doctor not an AI bot, 
            Keep your answer concise (max 2 sentences). No preamble, start your answer right away please"""

VOICE_ONLY_PROMPT = """You are DocBot, an AI Doctor assisting patients in a conversational, patient manner, like a phone call. Based on the patient's symptoms, respond naturally with proper punctuation for smooth text-to-speech delivery. Start by suggesting a possible cause of the symptoms, then ask relevant follow-up questions to gather more details, and stop there—do not provide advice or medication until the patient responds. internally the developer of your code has alloted u memory in whcih all the chat history will be loded into u after every call Use your memory of the conversation to build on previous responses, taking as many turns as needed to diagnose thoroughly,you can ask upto 2 to 3 questions to the pateint without rushing and after that move ahead confidently. Speak confidently and professionally, as a real doctor would
            """

# Configure upload folder
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads'))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Chat history file path
CHAT_HISTORY_FILE = os.environ.get('CHAT_HISTORY_FILE', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chat_history.json'))

# Load chat history from JSON file
def load_chat_history():
    try:
        if os.path.exists(CHAT_HISTORY_FILE):
            with open(CHAT_HISTORY_FILE, 'r') as f:
                history = json.load(f)
                if isinstance(history, list) and all(isinstance(item, dict) and 'role' in item and 'content' in item for item in history):
                    # Filter out messages with empty content
                    return [msg for msg in history if msg.get('content')]
        return []
    except Exception as e:
        print(f"Error loading chat history: {e}")
        return []

# Save chat history to JSON file
def save_chat_history(history):
    try:
        # Filter out messages with empty content before saving
        filtered_history = [msg for msg in history if msg.get('content')]
        with open(CHAT_HISTORY_FILE, 'w') as f:
            json.dump(filtered_history, f, indent=2)
    except Exception as e:
        print(f"Error saving chat history: {e}")

@app.route("/")
def home():
    return "Hello, world!"


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

@app.route('/api/patient-info', methods=['POST'])
def save_patient_info():
    data = request.json
    return jsonify({"status": "success", "data": data})

@app.route('/api/chat-history', methods=['GET'])
def get_chat_history():
    history = load_chat_history()
    return jsonify({"history": history})

@app.route('/api/clear-chat', methods=['POST'])
def clear_chat_history():
    save_chat_history([])
    return jsonify({"status": "success", "message": "Chat history cleared"})

@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({"error": "No audio file selected"}), 400
    
    filename = secure_filename(audio_file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    audio_file.save(filepath)
    
    transcript = transcribe_with_groq(
        stt_model="whisper-large-v3",
        audio_filepath=filepath,
        GROQ_API_KEY=GROQ_API_KEY
    )
    
    return jsonify({"transcript": transcript})

@app.route('/api/consultation', methods=['POST'])
def process_consultation():
    data = request.form
    files = request.files
    
    # Extract patient info
    patient_info = {}
    if 'patientInfo' in data:
        patient_info = json.loads(data['patientInfo'])
    
    # Build poll summary from patient info
    poll_summary = ""
    if patient_info:
        common = ", ".join(patient_info.get("common_conditions", []))
        other = patient_info.get("other_condition", "").strip()
        issue = patient_info.get("issue_type", "")
        specific = patient_info.get("specific_issue", "").strip()
        age = patient_info.get("age", "")
        gender = patient_info.get("gender", "")
        
        poll_summary = f"Patient conditions: {common}."
        if other:
            poll_summary += f" Other: {other}."
        poll_summary += f" Issue type: {issue}."
        if specific:
            poll_summary += f" Specific issue: {specific}."
        poll_summary += f" Age: {age}."
        poll_summary += f" Gender: {gender}."
    
    # Process user query
    user_query = data.get('query', '').strip()
    
    # Handle image upload
    image_filepath = None
    if 'image' in files:
        image_file = files['image']
        if image_file.filename != '':
            filename = secure_filename(image_file.filename)
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                filename += '.jpg'
            image_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_filepath)
            print(f"Image saved to {image_filepath}")
            # Verify image file exists and has content
            if os.path.exists(image_filepath) and os.path.getsize(image_filepath) > 0:
                print(f"Image file verified: {image_filepath} (size: {os.path.getsize(image_filepath)} bytes)")
            else:
                print(f"Warning: Image file verification failed for {image_filepath}")
                if os.path.exists(image_filepath):
                    print(f"File exists but size is {os.path.getsize(image_filepath)} bytes")
                else:
                    print(f"File does not exist after saving")
                image_filepath = None
    
    # Handle audio input
    audio_filepath = None
    transcript = ""
    if 'audio' in files:
        audio_file = files['audio']
        if audio_file.filename != '':
            filename = secure_filename(audio_file.filename)
            audio_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            audio_file.save(audio_filepath)
            transcript = transcribe_with_groq(
                stt_model="whisper-large-v3",
                audio_filepath=audio_filepath,
                GROQ_API_KEY=GROQ_API_KEY
            )
            if not user_query and transcript.strip():
                user_query = transcript.strip()
    
    # Fallback to patient info text query if no other input
    if not user_query and not image_filepath:
        user_query = patient_info.get("text_query", "").strip()
        if not user_query:
            return jsonify({"error": "Please provide a query via voice, text, or image"}), 400
    
    # Load existing chat history
    chat_history = load_chat_history()
    
    # Store the user query in chat history (text only for history display)
    # Only add non-empty messages to chat history
    if user_query.strip():
        chat_history.append({"role": "user", "content": user_query})
        save_chat_history(chat_history)
    
    # Construct conversation based on input type
    if image_filepath and os.path.exists(image_filepath):
        print(f"Processing image: {image_filepath}")
        encoded_img = encode_image(image_filepath)
        if not encoded_img:
            print(f"Error: Failed to encode image {image_filepath}")
            return jsonify({"error": "Failed to process the uploaded image"}), 500
            
        print(f"Image encoded successfully, size: {len(encoded_img)} characters")
        # Verify the encoded image format
        if len(encoded_img) < 100:
            print(f"Warning: Encoded image is suspiciously small: {len(encoded_img)} characters")
        
        # Check if the image is properly formatted for the API
        try:
            # Attempt to decode a small portion to verify it's valid base64
            base64.b64decode(encoded_img[:100])
            print("Base64 encoding validation passed")
        except Exception as e:
            print(f"Warning: Base64 validation failed: {str(e)}")
        
        # First, generate an image description using a separate API call
        image_description_prompt = "Describe this medical image in detail. What do you see?"
        
        # Create a multimodal message just for image description
        image_analysis_message = {
            "role": "user",
            "content": [
                {"type": "text", "text": image_description_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_img}"}}
            ]
        }
        
        # Get image description
        try:
            print("Generating image description...")
            image_description = analyze_image_with_query(
                query=image_description_prompt,
                model="llama-3.2-11b-vision-preview",
                encoded_image=encoded_img,
                api_key=GROQ_API_KEY
            )
            print(f"Generated image description: {image_description[:100]}...")
            
            # Add the image description to the user query
            enhanced_query = f"{user_query}\n\n[Image Description: {image_description}]"
            
            # Update the user message in chat history with the enhanced query that includes image description
            if chat_history and chat_history[-1]["role"] == "user":
                chat_history[-1]["content"] = enhanced_query
                save_chat_history(chat_history)
            
        except Exception as e:
            print(f"Error generating image description: {e}")
            enhanced_query = user_query
            image_description = ""
        
        text_part = MULTIMODAL_PROMPT + " " + poll_summary + " " + enhanced_query
        
        # Create a properly formatted multimodal message
        # The content must be an array of objects with type and text/image_url fields
        multimodal_message = {
            "role": "user",
            "content": [
                {"type": "text", "text": text_part},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_img}"}}
            ]
        }
        print(f"Created multimodal message with text and image")
        
        # For the model, we need to include the image, but we've already saved the text-only version to history
        # Convert previous chat history messages to proper format (string content only)
        formatted_history = []
        for msg in load_chat_history():
            # Ensure all previous messages have string content
            if isinstance(msg.get('content'), str):
                formatted_history.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        conversation = formatted_history + [multimodal_message]
    else:
        system_message = {"role": "system", "content": VOICE_ONLY_PROMPT}
        current_user_message = {"role": "user", "content": poll_summary + " " + user_query}
        conversation = [system_message] + chat_history + [current_user_message]
    
    # Filter out empty messages before sending to API
    filtered_conversation = [msg for msg in conversation if msg.get('content')]
    
    # Generate doctor's response
    try:
        print(f"Sending request to Groq API with model: llama-3.2-11b-vision-preview")
        
        # Use different approach based on whether we have an image or not
        if image_filepath and os.path.exists(image_filepath):
            print(f"Request includes image data - using analyze_image_with_query")
            # For image-based consultation, use the dedicated image analysis function
            # Extract the text part from the multimodal message
            text_part = multimodal_message['content'][0]['text']
            doctor_response = analyze_image_with_query(
                query=text_part,
                model="llama-3.2-11b-vision-preview",
                encoded_image=encoded_img,
                api_key=GROQ_API_KEY
            )
        else:
            # Check if the user query contains an image description from a previous message
            has_image_description = any("[Image Description:" in msg.get("content", "") for msg in chat_history if msg.get("role") == "user")
            
            # For text-only consultation, use the regular text function
            doctor_response = generate_doctor_response_text(
                query=filtered_conversation,
                model="llama-3.2-11b-vision-preview",
                api_key=GROQ_API_KEY
            )
            
            # If there was an image description in the chat history, make sure the response acknowledges it
            if has_image_description and "[Image Description:" not in doctor_response:
                print("Adding image context reminder to doctor's response")
                doctor_response = "Based on the image you've shared and your description, " + doctor_response
                
        print(f"Received response from Groq API: {doctor_response[:100]}...")
        
        # Update chat history (text only)

        chat_history.append({"role": "assistant", "content": doctor_response})
        save_chat_history(chat_history)
        
        # Prepare initial response
        response = {
            "transcript": transcript,
            "doctor_response": doctor_response,
            "audio_pending": True
        }
    except Exception as e:
        error_msg = f"Error generating doctor response: {e}"
        print(error_msg)
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception details: {str(e)}")
        
        # Check if this is a multimodal request that failed
        if image_filepath and os.path.exists(image_filepath):
            print(f"Error occurred with multimodal request (image processing)")
            
        return jsonify({"error": f"Failed to generate doctor response: {str(e)}"}), 500
    
    # Generate audio response
    audio_output_path = os.path.join(app.config['UPLOAD_FOLDER'], "doctor_response.mp3")
    try:
        text_to_speech_with_elevenlabs(
            input_text=doctor_response,
            output_filepath=audio_output_path,
            api_key=ELEVENLABS_API_KEY
        )
        with open(audio_output_path, "rb") as audio_file:
            audio_data = base64.b64encode(audio_file.read()).decode('utf-8')
        response.update({
            "audio_data": audio_data,
            "audio_pending": False
        })
    except Exception as e:
        print(f"Error generating audio response: {e}")
        response.update({"audio_error": "Failed to generate audio response"})
    
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)