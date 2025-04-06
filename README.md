# Medical Consultation API Server

This server provides the backend API for the medical consultation application, allowing integration with a React frontend.

## Setup Instructions

### Backend Setup

1. Create a virtual environment (recommended):
   ```
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the server directory with your API keys (see `.env.example` for reference):
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   ```

4. Create an uploads directory for storing temporary files:
   ```
   mkdir uploads
   ```

5. Start the Flask server:
   ```
   python app.py
   ```
   The server will run on http://localhost:8000

## Features

- Patient information collection
- Image-based medical analysis
- Voice transcription and processing
- Text-to-speech response generation
- Conversation history management

## Setup

1. Install dependencies:
   ```
   cd server
   pip install -r requirements.txt
   ```

2. Set environment variables (or they will use default values):
   ```
   export GROQ_API_KEY=your_groq_api_key
   ```

3. Run the server:
   ```
   python app.py
   ```

## API Endpoints

### Health Check
- **GET** `/api/health`
  - Returns server health status

### Patient Information
- **POST** `/api/patient-info`
  - Saves patient information
  - Body: JSON with patient details

### Audio Transcription
- **POST** `/api/transcribe`
  - Transcribes audio to text
  - Body: Form data with 'audio' file

### Consultation
- **POST** `/api/consultation`
  - Processes a complete consultation
  - Body: Form data with optional 'image', 'audio', 'query', and 'patientInfo'
  - Returns: Doctor's text response, audio response, and transcript

## Integration with React

To integrate with a React frontend, make API calls to these endpoints. Example:

```javascript
// Example of calling the consultation endpoint
async function submitConsultation(formData) {
  const response = await fetch('http://localhost:8000/api/consultation', {
    method: 'POST',
    body: formData,
  });
  return await response.json();
}
```