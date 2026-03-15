const axios = require('axios');
const fs = require('fs');
const FormData = require('form-data');

class FishAudioTranscriber {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.baseUrl = "https://api.fish.audio/v1/asr";

        if (!this.apiKey) {
            throw new Error("API Key is required.");
        }
    }

    async transcribe(audioFilePath, language = "en") {
        if (!fs.existsSync(audioFilePath)) {
            throw new Error(`Audio file not found: ${audioFilePath}`);
        }

        const formData = new FormData();
        formData.append('audio', fs.createReadStream(audioFilePath));
        formData.append('language', language);
        formData.append('ignore_timestamps', 'true');

        try {
            const response = await axios.post(this.baseUrl, formData, {
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    ...formData.getHeaders()
                }
            });

            return response.data;
        } catch (error) {
            console.error("Error during transcription:", error.message);
            if (error.response) {
                console.error("Response data:", error.response.data);
            }
            return null;
        }
    }
}

module.exports = FishAudioTranscriber;
