import { app, BrowserWindow, ipcMain } from 'electron'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import * as fs from 'fs'
import { spawn } from 'child_process'
import { config } from 'dotenv'
import { AudioRecorder } from './recorder'
import { PicovoiceTranscriber } from './transcriber'
import { TTSConfirmation } from './tts-confirmation'

// Load environment variables (app .env first, then root .env for ANTHROPIC_API_KEY etc.)
config({ path: path.join(path.dirname(fileURLToPath(import.meta.url)), '..', '.env') })
config({ path: path.join(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '.env') })

const require = createRequire(import.meta.url)
const __dirname = path.dirname(fileURLToPath(import.meta.url))

process.env.APP_ROOT = path.join(__dirname, '..')

export const VITE_DEV_SERVER_URL = process.env['VITE_DEV_SERVER_URL']
export const MAIN_DIST = path.join(process.env.APP_ROOT, 'dist-electron')
export const RENDERER_DIST = path.join(process.env.APP_ROOT, 'dist')

process.env.VITE_PUBLIC = VITE_DEV_SERVER_URL ? path.join(process.env.APP_ROOT, 'public') : RENDERER_DIST

let win: BrowserWindow | null
let recorder: AudioRecorder | null = null
let transcriber: PicovoiceTranscriber | null = null
let ttsConfirmation: TTSConfirmation | null = null
let agentProcess: ReturnType<typeof spawn> | null = null

function createWindow() {
  win = new BrowserWindow({
    icon: path.join(process.env.VITE_PUBLIC, 'electron-vite.svg'),
    width: 100,
    height: 100,
    transparent: true,
    frame: false,
    alwaysOnTop: true,
    hasShadow: false,
    resizable: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.mjs'),
    },
  })

  win.webContents.on('did-finish-load', () => {
    win?.webContents.send('main-process-message', (new Date).toLocaleString())
  })


  if (VITE_DEV_SERVER_URL) {
    win.loadURL(VITE_DEV_SERVER_URL)
  } else {
    win.loadFile(path.join(RENDERER_DIST, 'index.html'))
  }
}

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
    win = null
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})

// IPC Handlers for recording and transcription
ipcMain.handle('start-recording', async () => {
  try {
    // Initialize recorder and transcriber if not already done
    if (!recorder) {
      recorder = new AudioRecorder();
    }

    if (!transcriber) {
      const accessKey = process.env.VITE_PICOVOICE_ACCESS_KEY;
      if (!accessKey) {
        throw new Error('VITE_PICOVOICE_ACCESS_KEY not found in environment variables');
      }
      transcriber = new PicovoiceTranscriber(accessKey);
    }

    if (!ttsConfirmation) {
      const accessKey = process.env.VITE_PICOVOICE_ACCESS_KEY;
      if (!accessKey) {
        throw new Error('VITE_PICOVOICE_ACCESS_KEY not found in environment variables');
      }
      ttsConfirmation = new TTSConfirmation(accessKey);
    }

    // Create temp file path
    const tempDir = app.getPath('temp');
    const outputFile = path.join(tempDir, `recording_${Date.now()}.wav`);

    console.log('Starting recording...');

    // Start recording (will stop on silence)
    await recorder.startRecording(outputFile);

    // Notify renderer that recording stopped (user finished speaking)
    win?.webContents.send('recording-stopped');

    console.log('Recording complete, starting transcription...');
    console.log('Audio file path:', outputFile);
    console.log('File exists:', fs.existsSync(outputFile));
    if (fs.existsSync(outputFile)) {
      console.log('File size:', fs.statSync(outputFile).size, 'bytes');
    }

    // Transcribe the audio
    const result = await transcriber.transcribe(outputFile);

    // Clean up the temp file
    if (fs.existsSync(outputFile)) {
      fs.unlinkSync(outputFile);
    }

    if (result && (result.text || result.transcription)) {
      const transcribedText = (result.text || result.transcription) as string;
      console.log('Transcription:', transcribedText);

      // Play confirmation sound
      if (ttsConfirmation) {
        await ttsConfirmation.playConfirmation();
      }

      // Execute agent_s3.py with the transcribed text
      console.log('Executing Agent S3...');
      const appRoot = process.env.APP_ROOT || path.join(__dirname, '..');
      const agentScriptPath = path.join(appRoot, 'agent-s2-example', 'agent_s3.py');

      const pythonPath = process.platform === 'win32'
        ? path.join(process.env.APP_ROOT || '', '..', '.venv', 'Scripts', 'python.exe')
        : 'python3';

      win?.webContents.send('agent-started');

      await new Promise<void>((resolve, reject) => {
        agentProcess = spawn(pythonPath, ['-u', agentScriptPath, transcribedText], {
          env: process.env as NodeJS.ProcessEnv,
          stdio: ['inherit', 'pipe', 'pipe']
        });

        // Pipe stderr to console
        agentProcess.stderr?.on('data', (data: Buffer) => {
          process.stderr.write(data);
        });

        // Buffer stdout lines to capture NARRATION: prefixed lines for TTS
        let lineBuffer = '';
        agentProcess.stdout?.on('data', (data: Buffer) => {
          const text = data.toString('utf-8');
          process.stdout.write(text); // still print everything to console
          lineBuffer += text;
          const lines = lineBuffer.split('\n');
          lineBuffer = lines.pop() || ''; // keep incomplete line in buffer
          for (const line of lines) {
            if (line.startsWith('NARRATION:') && ttsConfirmation) {
              const narration = line.slice('NARRATION:'.length).trim();
              if (narration) {
                ttsConfirmation.speakText(narration).catch(err =>
                  console.error('Narration TTS error:', err.message)
                );
              }
            }
          }
        });

        agentProcess.on('close', async (code: number | null) => {
          // Flush any remaining buffered line
          if (lineBuffer.trim()) {
            process.stdout.write(lineBuffer + '\n');
            if (lineBuffer.startsWith('NARRATION:') && ttsConfirmation) {
              const narration = lineBuffer.slice('NARRATION:'.length).trim();
              if (narration) {
                await ttsConfirmation.speakText(narration).catch(err =>
                  console.error('Narration TTS error:', err.message)
                );
              }
            }
          }
          agentProcess = null;
          win?.webContents.send('agent-stopped');
          if (code === 0 || code === null) {
            console.log(code === null ? 'Agent S3 was stopped' : 'Agent S3 completed successfully');
            // Play completion notification
            if (code === 0 && ttsConfirmation) {
              try {
                await ttsConfirmation.speakText('All done!');
              } catch (err: any) {
                console.error('Completion TTS error:', err.message);
              }
            }
            resolve();
          } else {
            console.error(`Agent S3 exited with code ${code}`);
            reject(new Error(`Agent S3 exited with code ${code}`));
          }
        });

        agentProcess.on('error', (err: Error) => {
          agentProcess = null;
          win?.webContents.send('agent-stopped');
          console.error('Failed to start Agent S3:', err);
          reject(err);
        });
      });

      return { success: true, text: transcribedText, fullResult: result };
    } else {
      return { success: false, error: 'No transcription result' };
    }
  } catch (error: any) {
    console.error('Recording/Transcription/Agent error:', error);
    return { success: false, error: error.message };
  }
})

// Stop the running agent process
ipcMain.handle('stop-agent', async () => {
  if (agentProcess) {
    console.log('Stopping Agent S3...');
    agentProcess.kill();
    return { success: true };
  }
  return { success: false, error: 'No agent running' };
})

app.whenReady().then(createWindow)
