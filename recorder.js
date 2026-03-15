const fs = require('fs');
const { spawn } = require('child_process');

class AudioRecorder {
    constructor(options = {}) {
        this.threshold = options.threshold || 500; // Silence threshold
        this.silenceDuration = options.silenceDuration || 2000; // ms
        this.sampleRate = options.sampleRate || 16000; // SoX default often 16k, but can be 44100

        this.recordingProcess = null;
        this.silenceStart = null;
        this.isRecording = false;

        // Hardcoded path to SoX
        this.soxPath = 'C:\\Program Files (x86)\\sox-14-4-2\\sox.exe';
    }

    startRecording(outputFile) {
        return new Promise((resolve, reject) => {
            if (this.isRecording) {
                return reject(new Error("Already recording"));
            }

            if (!fs.existsSync(this.soxPath)) {
                return reject(new Error(`SoX not found at ${this.soxPath}. Please install SoX.`));
            }

            console.log("Listening... Speak now.");
            this.isRecording = true;
            this.silenceStart = null;

            const fileStream = fs.createWriteStream(outputFile, { encoding: 'binary' });

            // Spawn SoX directly
            const args = [
                '-t', 'waveaudio',      // Force Windows audio driver
                'default',              // Default device
                '-q',                   // Quiet mode (no show progress)
                '-r', this.sampleRate,  // Sample rate
                '-c', '1',              // Channels
                '-e', 'signed-integer', // Encoding
                '-b', '16',             // Bits
                '-t', 'wav',            // Output type
                '-'                     // Output to stdout
            ];

            console.log(`Spawning: "${this.soxPath}" ${args.join(' ')}`);

            this.recordingProcess = spawn(this.soxPath, args);

            const stream = this.recordingProcess.stdout;

            stream.pipe(fileStream);

            stream.on('data', (chunk) => {
                if (!this.isRecording) return;

                if (this.isSilent(chunk)) {
                    if (!this.silenceStart) {
                        this.silenceStart = Date.now();
                    } else if (Date.now() - this.silenceStart > this.silenceDuration) {
                        console.log("Silence detected.");
                        this.stopRecording();
                        resolve(outputFile);
                    }
                } else {
                    this.silenceStart = null;
                }
            });

            this.recordingProcess.stderr.on('data', (data) => {
                // SoX logs to stderr, useful for debugging but can be noisy
                console.error(`SoX stderr: ${data}`);
            });

            this.recordingProcess.on('error', (err) => {
                console.error("Audio process error:", err);
                this.stopRecording();
                reject(err);
            });

            this.recordingProcess.on('close', (code) => {
                if (code !== 0 && this.isRecording) {
                    console.log(`SoX process exited with code ${code}`);
                }
            });
        });
    }

    stopRecording() {
        if (this.isRecording) {
            this.isRecording = false;
            if (this.recordingProcess) {
                this.recordingProcess.kill(); // Send SIGTERM
                this.recordingProcess = null;
            }
            console.log("Recording stopped.");
        }
    }

    isSilent(buffer) {
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

module.exports = AudioRecorder;
