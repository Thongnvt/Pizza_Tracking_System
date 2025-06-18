import React, { useState, useEffect } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

interface VideoSelectorProps {
    onSelect: (videoSource: string) => void;
    onProcessChange: (isProcessing: boolean) => void;
    selectedZone: number | null;
}

const VideoSelector: React.FC<VideoSelectorProps> = ({ onSelect, onProcessChange, selectedZone }) => {
    const [videoSources, setVideoSources] = useState<string[]>([]);
    const [selectedSource, setSelectedSource] = useState<string>('');
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [isProcessing, setIsProcessing] = useState<boolean>(false);
    const [uploadedFile, setUploadedFile] = useState<File | null>(null);
    const [uploadedFilePath, setUploadedFilePath] = useState<string>('');
    const [isSourceReady, setIsSourceReady] = useState<boolean>(false);
    const [uploadProgress, setUploadProgress] = useState<number>(0);
    const [isUploading, setIsUploading] = useState<boolean>(false);

    useEffect(() => {
        const fetchVideoSources = async () => {
            try {
                setIsLoading(true);
                setError(null);
                const response = await fetch(`${API_BASE_URL}/api/video-sources`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                setVideoSources(data.sources);
            } catch (error) {
                console.error('Error fetching video sources:', error);
                setError('Failed to load video sources. Please check if the server is running.');
                setVideoSources([]);
            } finally {
                setIsLoading(false);
            }
        };

        fetchVideoSources();
    }, []);

    useEffect(() => {
        if (selectedSource === '1') {
            setIsSourceReady(true);
        } else if (selectedSource === '2' && uploadedFilePath) {
            setIsSourceReady(true);
        } else {
            setIsSourceReady(false);
        }
    }, [selectedSource, uploadedFilePath]);

    // Add cleanup effect for video processing
    useEffect(() => {
        return () => {
            // Cleanup when component unmounts
            if (isProcessing) {
                handleProcessToggle();
            }
        };
    }, [isProcessing]);

    const handleSourceChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const source = event.target.value;
        setSelectedSource(source);
        if (source !== '2') {
            setUploadedFile(null);
            setUploadedFilePath('');
            setUploadProgress(0);
        }
        onSelect(source);
    };

    const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        // Check if file is a video
        if (!file.type.startsWith('video/')) {
            setError('Please select a valid video file');
            return;
        }

        // Check file size (2GB limit)
        const maxSize = 2 * 1024 * 1024 * 1024; // 2GB in bytes
        if (file.size > maxSize) {
            setError('File size exceeds 2GB limit');
            return;
        }

        setUploadedFile(file);
        setError(null);
        setIsUploading(true);
        setUploadProgress(0);

        // Upload file to server
        const formData = new FormData();
        formData.append('video', file);

        try {
            const response = await fetch(`${API_BASE_URL}/api/upload-video`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to upload video');
            }

            const data = await response.json();
            setUploadedFilePath(data.videoPath);
            onSelect(data.videoPath);
            setUploadProgress(100);

            // Show success message
            console.log(`Video uploaded successfully: ${data.filename} (${(data.size / (1024 * 1024)).toFixed(1)}MB)`);

        } catch (error) {
            console.error('Error uploading video:', error);
            setError(error instanceof Error ? error.message : 'Failed to upload video. Please try again.');
            setUploadedFile(null);
            setUploadedFilePath('');
        } finally {
            setIsUploading(false);
        }
    };

    const handleProcessToggle = async () => {
        if (!selectedSource || !isSourceReady || !selectedZone) return;

        try {
            const source = selectedSource === '1' ? '0' : uploadedFilePath || selectedSource;

            const response = await fetch(`${API_BASE_URL}/api/process-toggle`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    source: source,
                    action: isProcessing ? 'stop' : 'start',
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to toggle processing');
            }

            setIsProcessing(!isProcessing);
            onProcessChange(!isProcessing);
        } catch (error) {
            console.error('Error toggling process:', error);
            setError(error instanceof Error ? error.message : 'Failed to toggle processing. Please try again.');
        }
    };

    const isProcessButtonEnabled = () => {
        if (isProcessing) return true; // Always enable when processing
        if (!selectedSource) return false;
        if (!isSourceReady) return false;
        if (!selectedZone) return false;
        return true;
    };

    const formatFileSize = (bytes: number) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    return (
        <div className="component-card">
            <h3>Video Source</h3>
            {isLoading ? (
                <div className="loading">Loading video sources...</div>
            ) : error ? (
                <div className="error">{error}</div>
            ) : (
                <>
                    <div className="source-selection">
                        <select
                            value={selectedSource}
                            onChange={handleSourceChange}
                            disabled={isProcessing}
                        >
                            <option value="">Select a video source</option>
                            <option value="1">Webcam</option>
                            <option value="2">Upload Video (up to 2GB)</option>
                        </select>

                        {selectedSource === '2' && (
                            <div className="file-upload">
                                <label className="file-upload-label">
                                    <input
                                        type="file"
                                        accept="video/*"
                                        onChange={handleFileUpload}
                                        disabled={isProcessing || isUploading}
                                    />
                                    <span>
                                        {isUploading ? 'Uploading...' : 'Upload Video File'}
                                    </span>
                                </label>
                                {uploadedFile && (
                                    <div className="uploaded-file">
                                        <strong>{uploadedFile.name}</strong>
                                        <br />
                                        Size: {formatFileSize(uploadedFile.size)}
                                        {isUploading && (
                                            <div className="upload-progress">
                                                <div
                                                    className="progress-bar"
                                                    style={{ width: `${uploadProgress}%` }}
                                                ></div>
                                                <span>{uploadProgress}%</span>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {!selectedZone && (
                        <div className="warning-message">
                            Please select a zone before starting processing
                        </div>
                    )}

                    <button
                        className={`process-button ${isProcessing ? 'stop' : 'start'}`}
                        onClick={handleProcessToggle}
                        disabled={!isProcessButtonEnabled()}
                    >
                        {isProcessing ? 'Stop Processing' : 'Start Processing'}
                    </button>
                </>
            )}
        </div>
    );
};

export default VideoSelector;
