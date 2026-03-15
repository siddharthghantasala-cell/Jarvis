import * as fs from 'fs';
import { spawn, ChildProcess } from 'child_process';

interface RecorderOptions {
    threshold?: number;
    silenceDuration?: number;
    sampleRate?: number;
}

export class AudioRecorder {
    private threshold: number;
    private silenceDuration: number;
    private sampleRate: number;
    private recordingProcess: ChildProcess | null = null;
    private silenceStart: number | null = null;
    private isRecording: boolean = false;

    constructor(options: RecorderOptions = {}) {
        this.threshold = options.threshold || 500; // Silence threshold
        this.silenceDuration = options.silenceDuration || 2000; // ms
        this.sampleRate = options.sampleRate || 16000;
    }

    startRecording(outputFile: string): Promise<string> {
        return new Promise((resolve, reject) => {
            if (this.isRecording) {
                return reject(new Error("Already recording"));
            }

            console.log("Listening... Speak now.");
            this.isRecording = true;
            this.silenceStart = null;

            const fileStream = fs.createWriteStream(outputFile, { encoding: 'binary' });

            // Windows: use waveaudio driver; macOS: use coreaudio; Linux: use -d (default)
            const platform = process.platform;
            const inputArgs = platform === 'win32'
                ? ['-t', 'waveaudio', 'default']
                : platform === 'darwin'
                ? ['-t', 'coreaudio', 'default']
                : ['-d'];

            const args = [
                ...inputArgs,
                '-q',                   // Quiet mode (no show progress)
                '-r', String(this.sampleRate),  // Sample rate
                '-c', '1',              // Channels (mono)
                '-e', 'signed-integer', // Encoding
                '-b', '16',             // Bits
                '-t', 'wav',            // Output type
                '-'                     // Output to stdout
            ];

            const soxPath = process.platform === 'win32'
                ? 'C:\\Program Files (x86)\\sox-14-4-2\\sox.exe'
                : 'sox';

            console.log(`Spawning: ${soxPath} ${args.join(' ')}`);

            this.recordingProcess = spawn(soxPath, args);

            const stream = this.recordingProcess.stdout;

            if (stream) {
                stream.pipe(fileStream);

                stream.on('data', (chunk: Buffer) => {
                    if (!this.isRecording) return;

                    if (this.isSilent(chunk)) {
                        if (!this.silenceStart) {
                            this.silenceStart = Date.now();
                        } else if (Date.now() - this.silenceStart > this.silenceDuration) {
                            console.log("Silence detected.");
                            this.stopRecording();
                            // Wait for the file stream to finish writing before resolving
                            fileStream.end(() => {
                                resolve(outputFile);
                            });
                        }
                    } else {
                        this.silenceStart = null;
                    }
                });
            }

            if (this.recordingProcess.stderr) {
                this.recordingProcess.stderr.on('data', (data: Buffer) => {
                    // SoX logs to stderr, useful for debugging but can be noisy
                    console.error(`SoX stderr: ${data}`);
                });
            }

            this.recordingProcess.on('error', (err: Error) => {
                console.error("Audio process error:", err);
                this.stopRecording();
                reject(err);
            });

            this.recordingProcess.on('close', (code: number | null) => {
                if (code !== 0 && this.isRecording) {
                    console.log(`SoX process exited with code ${code}`);
                }
            });
        });
    }

    stopRecording(): void {
        if (this.isRecording) {
            this.isRecording = false;
            if (this.recordingProcess) {
                this.recordingProcess.kill(); // Send SIGTERM
                this.recordingProcess = null;
            }
            console.log("Recording stopped.");
        }
    }

    private isSilent(buffer: Buffer): boolean {
        // Simple check: max absolute value in buffer
        // Buffer is 16-bit integers (Little Endian)
        for (let i = 0; i < buffer.length; i += 2) {
            if (i + 1 >= buffer.length) break;
            const val = buffer.readInt16LE(i);
            if (Math.abs(val) > this.threshold) {
                return false;
            }
        }
        return true;
    }
}
