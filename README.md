# Voice Transcriber

An iPhone app that records audio, transcribes it using OpenAI's Whisper API, and uploads the transcription to Snowflake.

## Features

- **Audio Recording**: Record high-quality audio using your iPhone's microphone
- **Playback**: Listen to your recordings directly in the app
- **AI Transcription**: Automatically transcribe audio using OpenAI's Whisper API
- **Cloud Storage**: Upload transcriptions to Snowflake for data analysis
- **Recording Management**: View, manage, and delete recordings
- **Offline Storage**: Recordings are stored locally until transcribed and uploaded

## Requirements

- iOS 16.0 or later
- Xcode 14.0 or later
- Swift 5.0 or later
- Active OpenAI API account with Whisper API access
- Active Snowflake account with appropriate credentials

## Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd test_repo
```

### 2. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-...your-key-here...

# Snowflake Configuration
SNOWFLAKE_ACCOUNT=your-account.us-east-1
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_DATABASE=YOUR_DATABASE
SNOWFLAKE_SCHEMA=YOUR_SCHEMA
SNOWFLAKE_WAREHOUSE=YOUR_WAREHOUSE
SNOWFLAKE_TABLE=transcriptions
```

### 3. Set Up Snowflake Table

Create a table in your Snowflake database to store transcriptions:

```sql
CREATE TABLE transcriptions (
    id VARCHAR(255) PRIMARY KEY,
    filename VARCHAR(500),
    recording_date TIMESTAMP,
    transcription TEXT,
    duration FLOAT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

Alternatively, the app can attempt to create the table automatically if it has the necessary permissions.

### 4. Open in Xcode

```bash
open VoiceTranscriber/VoiceTranscriber.xcodeproj
```

### 5. Configure Scheme Environment Variables

In Xcode:

1. Go to **Product** → **Scheme** → **Edit Scheme...**
2. Select **Run** in the left sidebar
3. Go to the **Arguments** tab
4. Under **Environment Variables**, add your credentials:
   - `OPENAI_API_KEY`
   - `SNOWFLAKE_ACCOUNT`
   - `SNOWFLAKE_USER`
   - `SNOWFLAKE_PASSWORD`
   - `SNOWFLAKE_DATABASE`
   - `SNOWFLAKE_SCHEMA`
   - `SNOWFLAKE_WAREHOUSE`
   - `SNOWFLAKE_TABLE` (optional, defaults to "transcriptions")

### 6. Build and Run

1. Select your target device or simulator
2. Press **Cmd + R** to build and run

## Usage

### Recording Audio

1. Grant microphone permission when prompted
2. Tap the large circular button to start recording
3. Tap the square button to stop recording
4. Your recording will appear in the list below

### Transcribing

1. Tap on a recording in the list to view details
2. Tap **"Transcribe with OpenAI"** to send the audio to OpenAI's Whisper API
3. Wait for the transcription to complete (this may take a few seconds)
4. The transcription will be displayed in the detail view

### Uploading to Snowflake

1. After transcribing a recording, tap **"Upload to Snowflake"**
2. The transcription will be uploaded to your configured Snowflake table
3. A checkmark will appear next to uploaded recordings

### Playback

1. Tap on a recording to view details
2. Use the **"Play Recording"** button to listen
3. Use the **"Stop"** button to stop playback

## Architecture

### Project Structure

```
VoiceTranscriber/
├── VoiceTranscriberApp.swift    # App entry point
├── Config.swift                 # Configuration management
├── Info.plist                   # App permissions and settings
├── Models/
│   └── Recording.swift          # Recording data model
├── Services/
│   ├── AudioRecorderManager.swift  # Audio recording/playback
│   ├── OpenAIService.swift         # OpenAI Whisper integration
│   └── SnowflakeService.swift      # Snowflake upload service
└── Views/
    ├── ContentView.swift           # Main view with recording list
    └── RecordingDetailView.swift   # Recording detail and actions
```

### Key Components

#### AudioRecorderManager

Manages audio recording and playback using AVFoundation:
- Records audio in high-quality M4A format
- Handles microphone permissions
- Persists recordings to local storage
- Manages playback controls

#### OpenAIService

Integrates with OpenAI's Whisper API:
- Uploads audio files for transcription
- Handles multipart form data requests
- Returns transcribed text
- Error handling for API failures

#### SnowflakeService

Manages data upload to Snowflake:
- Uses Snowflake's SQL REST API
- Supports basic authentication
- Creates tables if needed (with proper permissions)
- Uploads transcription data with metadata

## Configuration

### OpenAI API

- **API Key**: Get your key from [OpenAI Platform](https://platform.openai.com/api-keys)
- **Model**: Uses `whisper-1` (configurable in Config.swift)
- **Pricing**: Check [OpenAI Pricing](https://openai.com/pricing) for Whisper API costs

### Snowflake

- **Account Identifier**: Format is `<account>.<region>` (e.g., `abc12345.us-east-1`)
- **Authentication**: Uses basic auth (username/password)
- **SQL API**: Uses Snowflake's REST API for SQL statements
- **Permissions**: User needs INSERT permissions on the target table

## Data Flow

1. **Recording**: Audio is captured and saved as M4A file locally
2. **Transcription**: Audio file is sent to OpenAI Whisper API
3. **Storage**: Transcription text is stored with the Recording model
4. **Upload**: Recording metadata and transcription are inserted into Snowflake

## Security Considerations

- API keys are stored in environment variables (not in code)
- `.env` file is gitignored to prevent credential leaks
- Snowflake credentials use basic authentication (consider OAuth for production)
- Audio files are stored locally on the device
- All API calls use HTTPS

## Troubleshooting

### Microphone Permission Denied

Go to **Settings** → **Privacy & Security** → **Microphone** and enable access for Voice Transcriber.

### OpenAI API Errors

- Verify your API key is correct and active
- Check you have sufficient credits in your OpenAI account
- Ensure audio files are in a supported format (M4A/AAC)

### Snowflake Upload Failures

- Verify all Snowflake credentials are correct
- Ensure the database, schema, and warehouse exist
- Check user has INSERT permissions on the target table
- Verify the Snowflake account identifier format

### Configuration Warning

If you see the orange configuration warning:
1. Verify all environment variables are set in Xcode scheme
2. Restart the app after setting environment variables
3. Check for typos in variable names

## Future Enhancements

- [ ] Support for multiple audio formats
- [ ] Batch transcription processing
- [ ] Cloud storage for audio files (S3, Azure Blob)
- [ ] Support for other transcription services
- [ ] OAuth authentication for Snowflake
- [ ] Export transcriptions to CSV/JSON
- [ ] Search and filter recordings
- [ ] Speaker diarization
- [ ] Real-time transcription

## License

MIT License - feel free to use this project for your own purposes.

## Credits

Built with:
- SwiftUI for the user interface
- AVFoundation for audio recording/playback
- OpenAI Whisper API for transcription
- Snowflake SQL API for data storage

## Support

For issues or questions, please open an issue on the GitHub repository.
