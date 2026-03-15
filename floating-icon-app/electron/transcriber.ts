import { createRequire } from 'node:module';
import * as fs from 'fs';

const require = createRequire(import.meta.url);
const { Leopard } = require('@picovoice/leopard-node');

interface TranscriptionResult {
    text: string;
}

export class PicovoiceTranscriber {
    private accessKey: string;

    constructor(accessKey: string) {
        this.accessKey = accessKey;
    }

    async transcribe(audioFilePath: string): Promise<TranscriptionResult | null> {
        const leopard = new Leopard(this.accessKey);
        try {
            // Read the WAV file and extract raw PCM data (skip 44-byte WAV header)
            // SoX streaming to stdout can produce malformed WAV headers,
            // so we read the raw PCM and use leopard.process() instead of processFile()
            const fileBuffer = fs.readFileSync(audioFilePath);
            const pcmBytes = fileBuffer.subarray(44);
            // Copy into a fresh ArrayBuffer to ensure proper alignment
            const alignedBuffer = new ArrayBuffer(pcmBytes.length);
            new Uint8Array(alignedBuffer).set(pcmBytes);
            const pcmData = new Int16Array(alignedBuffer);

            console.log(`PCM samples: ${pcmData.length}, duration: ${(pcmData.length / 16000).toFixed(1)}s`);

            const { transcript } = leopard.process(pcmData);
            return { text: transcript };
        } catch (error: any) {
            console.error('Error during transcription:', error.message);
            return null;
        } finally {
            leopard.release();
        }
    }
}
