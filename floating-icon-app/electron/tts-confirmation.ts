import { createRequire } from 'node:module';
import { writeFile, unlink } from 'fs/promises';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';
import { app } from 'electron';

const require = createRequire(import.meta.url);
const { Orca } = require('@picovoice/orca-node');

const execAsync = promisify(exec);

export class TTSConfirmation {
    private accessKey: string;
    private affirmativePhrases: string[] = [
        "Got it!",
        "On it!",
        "Sure thing!",
        "Understood!",
        "Will do!",
        "Okay!",
        "Roger that!",
        "Absolutely!",
        "You got it!",
        "Right away!"
    ];

    constructor(accessKey: string) {
        this.accessKey = accessKey;
    }

    async playConfirmation(): Promise<void> {
        const phrase = this.affirmativePhrases[Math.floor(Math.random() * this.affirmativePhrases.length)];
        console.log(`Playing confirmation: "${phrase}"`);
        await this.speakText(phrase);
    }

    async speakText(text: string): Promise<void> {
        const orca = new Orca(this.accessKey);
        try {
            const { pcm } = orca.synthesize(text);
            const sampleRate = orca.sampleRate;

            const tempDir = app.getPath('temp');
            const audioPath = path.join(tempDir, `tts_${Date.now()}.wav`);

            await writeFile(audioPath, pcmToWav(pcm, sampleRate));

            if (process.platform === 'darwin') {
                await execAsync(`afplay "${audioPath}"`);
            } else if (process.platform === 'win32') {
                await execAsync(`powershell -c "[System.Media.SoundPlayer]::new('${audioPath}').PlaySync()"`);
            } else {
                await execAsync(`aplay "${audioPath}"`);
            }

            await unlink(audioPath);
            console.log(`✓ TTS played: "${text.substring(0, 50)}..."`);
        } catch (error: any) {
            console.error('Error playing TTS:', error.message);
        } finally {
            orca.release();
        }
    }
}

function pcmToWav(pcm: Int16Array, sampleRate: number): Buffer {
    const numChannels = 1;
    const bitsPerSample = 16;
    const dataSize = pcm.length * 2;
    const buffer = Buffer.alloc(44 + dataSize);

    buffer.write('RIFF', 0);
    buffer.writeUInt32LE(36 + dataSize, 4);
    buffer.write('WAVE', 8);
    buffer.write('fmt ', 12);
    buffer.writeUInt32LE(16, 16);
    buffer.writeUInt16LE(1, 20);
    buffer.writeUInt16LE(numChannels, 22);
    buffer.writeUInt32LE(sampleRate, 24);
    buffer.writeUInt32LE(sampleRate * numChannels * bitsPerSample / 8, 28);
    buffer.writeUInt16LE(numChannels * bitsPerSample / 8, 32);
    buffer.writeUInt16LE(bitsPerSample, 34);
    buffer.write('data', 36);
    buffer.writeUInt32LE(dataSize, 40);

    for (let i = 0; i < pcm.length; i++) {
        buffer.writeInt16LE(pcm[i], 44 + i * 2);
    }

    return buffer;
}