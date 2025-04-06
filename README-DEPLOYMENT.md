# MedTech Deployment Guide

## Environment Setup

This application requires specific environment variables to be set for proper operation. These variables include API keys for external services and configuration options for file storage.

### Required Environment Variables

- `GROQ_API_KEY`: Your Groq API key for AI text generation and image analysis
- `ELEVENLABS_API_KEY`: Your ElevenLabs API key for text-to-speech conversion

### Optional Environment Variables

- `UPLOAD_FOLDER`: Custom path for uploaded files (default: `./uploads`)
- `CHAT_HISTORY_FILE`: Custom path for chat history storage (default: `./chat_history.json`)

## Setting Up Environment Variables

### Local Development

1. Create a `.env` file in the server directory with the following content:

```
GROQ_API_KEY=your_groq_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

2. Replace the placeholder values with your actual API keys

### Production Deployment

For production environments, set these environment variables according to your hosting platform:

#### Heroku

```bash
heroku config:set GROQ_API_KEY=your_groq_api_key_here
heroku config:set ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

#### Docker

Add these environment variables to your Docker Compose file or Docker run command:

```yaml
environment:
  - GROQ_API_KEY=your_groq_api_key_here
  - ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

#### Other Platforms

Consult your hosting platform's documentation for setting environment variables.

## File Storage Configuration

By default, the application stores uploaded files in the `uploads` directory and chat history in `chat_history.json`. For production deployments, consider:

1. Using environment variables to specify alternative storage locations
2. Implementing cloud storage for uploaded files (requires code modifications)
3. Using a database for chat history instead of file storage (requires code modifications)

## Starting the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py
```

The server will start on port 5000 by default.

## Troubleshooting

### Missing API Keys

If you see warnings about missing API keys, check that your environment variables are correctly set and accessible to the application.

### File Permission Issues

Ensure that the application has write permissions to the `uploads` directory and the location of `chat_history.json`.

### Cross-Origin Resource Sharing (CORS)

If you're hosting the frontend and backend on different domains, you may need to configure CORS settings in `app.py`.