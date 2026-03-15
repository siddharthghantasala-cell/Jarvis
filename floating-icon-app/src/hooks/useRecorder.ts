import { useState, useRef, useEffect } from 'react';

interface UseRecorderProps {
    onSilence?: (blob: Blob) => void;
    silenceDuration?: number;
    silenceThreshold?: number;
}

export const useRecorder = ({
    onSilence,
    silenceDuration = 2000,
    silenceThreshold = 0.02, // Adjusted for Web Audio API (0-1 range)
}: UseRecorderProps = {}) => {
    const [isRecording, setIsRecording] = useState(false);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const silenceStartRef = useRef<number | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);
    const animationFrameRef = useRef<number | null>(null);

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            // Setup MediaRecorder
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorder.start();
            setIsRecording(true);

            // Setup AudioContext for silence detection
            const audioContext = new AudioContext();
            audioContextRef.current = audioContext;
            const source = audioContext.createMediaStreamSource(stream);
            const analyser = audioContext.createAnalyser();
            analyser.fftSize = 2048;
            source.connect(analyser);
            analyserRef.current = analyser;

            detectSilence();

        } catch (error) {
            console.error("Error starting recording:", error);
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
            mediaRecorderRef.current.stop();
            mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());

            // Wait for the last data chunk
            mediaRecorderRef.current.onstop = () => {
                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' }); // Or 'audio/wav' if supported
                if (onSilence) {
                    onSilence(audioBlob);
                }
            };
        }

        if (audioContextRef.current) {
            audioContextRef.current.close();
        }
        if (animationFrameRef.current) {
            cancelAnimationFrame(animationFrameRef.current);
        }

        setIsRecording(false);
        silenceStartRef.current = null;
    };

    const detectSilence = () => {
        if (!analyserRef.current || !mediaRecorderRef.current || mediaRecorderRef.current.state !== 'recording') return;

        const bufferLength = analyserRef.current.fftSize;
        const dataArray = new Float32Array(bufferLength);
        analyserRef.current.getFloatTimeDomainData(dataArray);

        let isSilent = true;
        for (let i = 0; i < bufferLength; i++) {
            if (Math.abs(dataArray[i]) > silenceThreshold) {
                isSilent = false;
                break;
            }
        }

        if (isSilent) {
            if (!silenceStartRef.current) {
                silenceStartRef.current = Date.now();
            } else if (Date.now() - silenceStartRef.current > silenceDuration) {
                console.log("Silence detected, stopping recording...");
                stopRecording();
                return;
            }
        } else {
            silenceStartRef.current = null;
        }

        animationFrameRef.current = requestAnimationFrame(detectSilence);
    };

    // Cleanup
    useEffect(() => {
        return () => {
            if (isRecording) {
                stopRecording();
            }
        };
    }, []);

    return { startRecording, stopRecording, isRecording };
};
