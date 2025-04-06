# Medical Consultation Application - Server & Client

This project provides a complete solution for medical consultations, with a Flask backend server and React frontend. It replaces the original Gradio interface while maintaining all functionality.

## Features

- Patient information collection
- Image-based medical analysis using Groq LLM
- Voice recording and transcription
- Text-to-speech doctor responses using ElevenLabs
- Conversation history tracking

## Project Structure

```
server/
├── app.py                # Flask server with API endpoints
├── requirements.txt      # Python dependencies
├── uploads/              # Directory for uploaded files (created automatically)
├── client/               # React frontend application
│   ├── public/           # Static files
│   ├── src/              # React source code
│   └── package.json      # Node.js dependencies
└── README.md            # Server documentation
```

## Setup Instructions

### Backend Setup

1. Navigate to the server directory:
   ```
   cd server
   ```

2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set environment variables (optional, defaults are provided):
   ```
   export GROQ_API_KEY=your_groq_api_key
   ```

4. Start the Flask server:
   ```
   python app.py
   ```
   The server will run on http://localhost:8000

### Frontend Setup

1. Navigate to the client directory:
   ```
   cd server/client
   ```

2. Install Node.js dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm start
   ```
   The React app will run on http://localhost:3000

## API Endpoints

- **GET** `/api/health` - Health check endpoint
- **POST** `/api/patient-info` - Save patient information
- **POST** `/api/transcribe` - Transcribe audio to text
- **POST** `/api/consultation` - Process a complete consultation

## Development Notes

- The Flask server imports functionality from the original Python modules
- The React frontend provides a modern UI alternative to the Gradio interface
- All API calls from React to Flask are proxied through the development server