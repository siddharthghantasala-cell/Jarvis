require('dotenv').config();
const readline = require('readline');
const AudioRecorder = require('./recorder');
const FishAudioTranscriber = require('./transcriber');
const fs = require('fs');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

function askQuestion(query) {
    return new Promise(resolve => rl.question(query, resolve));
}

async function main() {
    console.log("FishAudio STT Demo (Node.js)");
    console.log("----------------------------");

    let apiKey = process.env.FISH_AUDIO_API_KEY;
    if (!apiKey) {
        console.log("Please set the FISH_AUDIO_API_KEY environment variable or .env file.");
        apiKey = await askQuestion("Enter your FishAudio API Key: ");
        if (!apiKey) {
            console.log("API Key is required.");
            rl.close();
            return;
        }
    }

    const recorder = new AudioRecorder();
    const transcriber = new FishAudioTranscriber(apiKey);
    const outputFile = "recorded_audio_js.wav";

    try {
        // 1. Record
        console.log("\nStep 1: Recording");
        await recorder.startRecording(outputFile);

        // 2. Transcribe
        console.log("\nStep 2: Transcribing");
        const result = await transcriber.transcribe(outputFile);

        if (result) {
            console.log("\nTranscription Result:");
            console.log(JSON.stringify(result, null, 2));

            if (result.text) {
                console.log(`\nText: ${result.text}`);
            } else if (result.transcription) {
                console.log(`\nText: ${result.transcription}`);
            }
        }

    } catch (error) {
        console.error("An error occurred:", error);
    } finally {
        rl.close();
        // Cleanup
        // if (fs.existsSync(outputFile)) fs.unlinkSync(outputFile);
    }
}

main();
