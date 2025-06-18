import React, { useEffect, useState } from 'react';
import { socket } from '../socket';

interface ProcessingStatus {
    source: string;
    status: string;
    message: string;
}

interface CountsUpdate {
    pending_boxes: number;
    boxes_sold: number;
    timestamp: string;
}

const StatusBar: React.FC = () => {
    const [processingStatus, setProcessingStatus] = useState<ProcessingStatus | null>(null);
    const [counts, setCounts] = useState<CountsUpdate | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [currentTime, setCurrentTime] = useState(new Date());

    useEffect(() => {
        // Update current time every second
        const timeInterval = setInterval(() => {
            setCurrentTime(new Date());
        }, 1000);

        // Connection status
        const handleConnect = () => {
            setIsConnected(true);
        };

        const handleDisconnect = () => {
            setIsConnected(false);
        };

        // Processing status updates
        const handleProcessingStatus = (data: ProcessingStatus) => {
            setProcessingStatus(data);
        };

        // Counts updates
        const handleCountsUpdate = (data: CountsUpdate) => {
            setCounts(data);
        };

        // Socket event listeners
        socket.on('connect', handleConnect);
        socket.on('disconnect', handleDisconnect);
        socket.on('processing_status', handleProcessingStatus);
        socket.on('counts_update', handleCountsUpdate);

        // Cleanup
        return () => {
            clearInterval(timeInterval);
            socket.off('connect', handleConnect);
            socket.off('disconnect', handleDisconnect);
            socket.off('processing_status', handleProcessingStatus);
            socket.off('counts_update', handleCountsUpdate);
        };
    }, []);

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'started':
            case 'processing':
                return 'text-blue-600';
            case 'completed':
                return 'text-green-600';
            case 'stopped':
                return 'text-yellow-600';
            case 'error':
                return 'text-red-600';
            default:
                return 'text-gray-600';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'started':
            case 'processing':
                return '⚙️';
            case 'completed':
                return '✅';
            case 'stopped':
                return '⏹️';
            case 'error':
                return '❌';
            default:
                return '📋';
        }
    };

    return (
        <div className="bg-white border-b border-gray-200 px-4 py-3">
            <div className="flex items-center justify-between">
                {/* Left side - Connection and Processing Status */}
                <div className="flex items-center space-x-6">
                    {/* Connection Status */}
                    <div className="flex items-center space-x-2">
                        <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                        <span className="text-sm text-gray-600">
                            {isConnected ? 'Connected' : 'Disconnected'}
                        </span>
                    </div>

                    {/* Processing Status */}
                    {processingStatus && (
                        <div className="flex items-center space-x-2">
                            <span className="text-lg">{getStatusIcon(processingStatus.status)}</span>
                            <div>
                                <span className={`text-sm font-medium ${getStatusColor(processingStatus.status)}`}>
                                    {processingStatus.status.charAt(0).toUpperCase() + processingStatus.status.slice(1)}
                                </span>
                                <div className="text-xs text-gray-500">
                                    {processingStatus.message}
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Right side - Counts and Time */}
                <div className="flex items-center space-x-6">
                    {/* Box Counts */}
                    {counts && (
                        <div className="flex items-center space-x-4">
                            <div className="flex items-center space-x-1">
                                <span className="text-yellow-500">⏳</span>
                                <span className="text-sm text-gray-600">
                                    Pending: <span className="font-medium">{counts.pending_boxes}</span>
                                </span>
                            </div>
                            <div className="flex items-center space-x-1">
                                <span className="text-green-500">📦</span>
                                <span className="text-sm text-gray-600">
                                    Sold: <span className="font-medium">{counts.boxes_sold}</span>
                                </span>
                            </div>
                        </div>
                    )}

                    {/* Current Time */}
                    <div className="text-sm text-gray-600">
                        {currentTime.toLocaleTimeString()}
                    </div>
                </div>
            </div>

            {/* Progress Bar for Processing */}
            {processingStatus && (processingStatus.status === 'processing' || processingStatus.status === 'started') && (
                <div className="mt-2">
                    <div className="w-full bg-gray-200 rounded-full h-1">
                        <div className="bg-blue-500 h-1 rounded-full animate-pulse" style={{ width: '100%' }}></div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default StatusBar;
