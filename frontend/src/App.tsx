import React, { useState, useEffect } from 'react';
import './App.css';
import StatusBar from './components/StatusBar';
import VideoSelector from './components/VideoSelector';
import VideoDisplay from './components/VideoDisplay';
import DetectionLog from './components/DetectionLog';
import DispatchZoneInfo from './components/DispatchZoneInfo';
import BoxStatistics from './components/BoxStatistics';
import { socket } from './socket';

function App() {
  const [selectedVideo, setSelectedVideo] = useState<string>('');
  const [selectedZone, setSelectedZone] = useState<number | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [isSourceReady, setIsSourceReady] = useState<boolean>(false);
  const [processingStatus, setProcessingStatus] = useState<string>('idle'); // 'idle', 'processing', 'completed', 'error'

  const handleVideoSelect = (videoSource: string) => {
    setSelectedVideo(videoSource);
    setProcessingStatus('idle');
    socket.emit('join_video', { source: videoSource });
  };

  const handleProcessChange = (processing: boolean) => {
    setIsProcessing(processing);
    if (!processing && isProcessing) {
      // Processing was stopped
      setProcessingStatus('completed');
    } else if (processing) {
      // Processing was started
      setProcessingStatus('processing');
    }
  };

  const handleZoneSelect = (zoneId: number) => {
    setSelectedZone(zoneId);
  };

  // Reset processing state when video source changes
  useEffect(() => {
    if (isProcessing) {
      setIsProcessing(false);
      setProcessingStatus('idle');
    }
  }, [selectedVideo]);

  // Reset zone selection when video source changes
  useEffect(() => {
    setSelectedZone(null);
  }, [selectedVideo]);

  return (
    <div className="app">
      <StatusBar />
      <div className="main-content">
        <div className="left-sidebar">
          <VideoSelector
            onSelect={handleVideoSelect}
            onProcessChange={handleProcessChange}
            selectedZone={selectedZone}
          />
          <BoxStatistics />
        </div>

        <div className="center-content">
          <VideoDisplay
            videoSource={selectedVideo}
            isProcessing={isProcessing}
            processingStatus={processingStatus}
          />
        </div>

        <div className="right-sidebar">
          <DetectionLog />
          <DispatchZoneInfo
            selectedZone={selectedZone}
            onZoneSelect={handleZoneSelect}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
