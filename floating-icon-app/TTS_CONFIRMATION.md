# TTS Confirmation Feature

## Overview
After a successful recording and transcription, the app now plays an affirmative phrase using Fish Audio's Text-to-Speech API to confirm that the recording was captured successfully.

## How It Works

1. **Recording completes** → Audio is transcribed
2. **Transcription succeeds** → Random affirmative phrase is selected
3. **TTS generates audio** → Fish Audio converts phrase to speech
4. **Audio plays** → Confirmation is played using macOS `afplay`
5. **Agent S3 executes** → The transcribed command is processed

## Affirmative Phrases

The system randomly selects from these phrases:
- "Got it"
- "On it"
- "Sure thing"
- "Understood"
- "Will do"
- "Okay"
- "Roger that"
- "Absolutely"
- "You got it"
- "Right away"

## Configuration

Make sure your `.env` file contains:
```
FISH_AUDIO_API_KEY=your_api_key_here
```

## Voice Customization

You can customize the voice by editing `electron/tts-confirmation.ts`. There are two ways to do this:

### Method 1: Edit the default voiceConfig (lines 35-40)

Uncomment and modify the voice settings:

```typescript
private voiceConfig: VoiceConfig = {
    referenceId: "7f92f8afb8ec43bf81429cc1c9199cb1", // Browse voices at https://fish.audio
    model: "v3-turbo", // Options: "speech-1.5", "speech-1.6", "v3-turbo", "v3-hd"
    emotion: "happy", // Only for v3 models: "happy", "sad", "angry", "calm", "auto", etc.
    format: "mp3"
};
```

### Method 2: Pass config when initializing (in main.ts)

```typescript
ttsConfirmation = new TTSConfirmation(apiKey, {
    referenceId: "your_voice_id_here",
    model: "v3-turbo",
    emotion: "calm"
});
```

### Finding Voice IDs

1. Visit [fish.audio](https://fish.audio)
2. Browse the voice library
3. Click on a voice you like
4. Copy the `reference_id` from the URL or voice card
5. Paste it into the `referenceId` field

### Available Options

- **referenceId**: Unique ID for a specific voice from fish.audio
- **model**: TTS engine version
  - `speech-1.5` - Standard quality
  - `speech-1.6` - Improved quality  
  - `v3-turbo` - Fast with emotion control
  - `v3-hd` - High quality with emotion control
- **emotion** (v3 models only): `happy`, `sad`, `angry`, `fearful`, `disgusted`, `surprised`, `calm`, `fluent`, `auto`
- **format**: `mp3`, `wav`, `pcm`, `opus`


## Customization

You can add custom phrases programmatically:
```typescript
ttsConfirmation.addPhrases(["Custom phrase 1", "Custom phrase 2"]);
```

## Error Handling

If TTS confirmation fails (e.g., network issues, API errors), the error is logged but **does not** interrupt the workflow. The Agent S3 execution will continue regardless.

## Files Modified

- **electron/tts-confirmation.ts** - New TTS confirmation module
- **electron/main.ts** - Integrated TTS into recording flow
- **package.json** - Added `fish-audio` dependency
