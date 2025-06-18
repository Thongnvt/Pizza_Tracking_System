import React, { useEffect, useRef, useState } from 'react';
import { socket } from '../socket';

interface VideoDisplayProps {
    videoSource: string;
    isProcessing: boolean;
    processingStatus?: string; // 'idle', 'processing', 'completed', 'error'
}

const VideoDisplay: React.FC<VideoDisplayProps> = ({ videoSource, isProcessing, processingStatus = 'idle' }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [isConnected, setIsConnected] = useState<boolean>(false);
    const [currentFrame, setCurrentFrame] = useState<string | null>(null);

    // Socket event handlers
    useEffect(() => {
        const handleConnect = () => {
            setIsConnected(true);
        };

        const handleDisconnect = () => {
            setIsConnected(false);
        };

        const handleVideoFrame = (data: { source: string; frame: string; frame_count: number }) => {
            setCurrentFrame(data.frame);
            // Detections are now drawn directly on the frame by the backend
        };

        // Add event listeners
        socket.on('connect', handleConnect);
        socket.on('disconnect', handleDisconnect);
        socket.on('video_frame', handleVideoFrame);

        // Cleanup function
        return () => {
            socket.off('connect', handleConnect);
            socket.off('disconnect', handleDisconnect);
            socket.off('video_frame', handleVideoFrame);
        };
    }, []); // Empty dependency array - only run once on mount

    // Canvas rendering effect
    useEffect(() => {
        if (!canvasRef.current || !currentFrame) return;

        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const img = new Image();
        img.onload = () => {
            // Set canvas size to match image
            canvas.width = img.width;
            canvas.height = img.height;

            // Draw the frame (detections are already drawn by the backend)
            ctx.drawImage(img, 0, 0);
        };

        // The currentFrame is already base64 encoded from the backend
        img.src = `data:image/jpeg;base64,${currentFrame}`;
    }, [currentFrame]); // Only depend on currentFrame

    // Show processing completed message
    if (processingStatus === 'completed') {
        return (
            <div className="video-display">
                <div className="processing-completed">
                    <h3>✅ Video Processing Completed Successfully!</h3>
                    <p>The video has been processed and analyzed.</p>
                    <p>Detection results have been saved.</p>
                </div>
            </div>
        );
    }

    // Show processing error message
    if (processingStatus === 'error') {
        return (
            <div className="video-display">
                <div className="processing-error">
                    <h3>❌ Video Processing Error</h3>
                    <p>An error occurred during video processing.</p>
                    <p>Please try again or check the video file.</p>
                </div>
            </div>
        );
    }

    if (!videoSource) {
        return (
            <div className="video-display">
                <div className="no-video-message">
                    <h3>📹 Select a Video Source</h3>
                    <p>Choose a video file or webcam to start processing</p>
                </div>
            </div>
        );
    }

    if (!isConnected) {
        return (
            <div className="video-display">
                <div className="connection-message">
                    <h3>🔄 Connecting to Video Stream...</h3>
                    <p>Establishing connection to the video processing server</p>
                </div>
            </div>
        );
    }

    if (isProcessing && !currentFrame) {
        return (
            <div className="video-display">
                <div className="processing-message">
                    <h3>⚙️ Processing Video...</h3>
                    <p>Analyzing video frames and detecting objects</p>
                    <div className="loading-spinner"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="video-display">
            <canvas ref={canvasRef} />
            {isProcessing && (
                <div className="processing-overlay">
                    <div className="processing-indicator">
                        <span>Processing...</span>
                    </div>
                </div>
            )}
        </div>
    );
};

export default VideoDisplay;
