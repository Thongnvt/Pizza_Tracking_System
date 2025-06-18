import React, { useEffect, useState } from 'react';
import { socket } from '../socket';

interface DetectionEvent {
    timestamp: string;
    type: string;
    details: string;
    source?: string;
    frame?: number;
}

interface LogMessage {
    message: string;
    timestamp: string;
}

interface CountsUpdate {
    pending_boxes: number;
    boxes_sold: number;
    timestamp: string;
}

const DetectionLog: React.FC = () => {
    const [events, setEvents] = useState<DetectionEvent[]>([]);
    const [logMessages, setLogMessages] = useState<LogMessage[]>([]);
    const [counts, setCounts] = useState<CountsUpdate | null>(null);
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        // Connection status
        const handleConnect = () => {
            setIsConnected(true);
            addEvent('system', 'Connected to server');
        };

        const handleDisconnect = () => {
            setIsConnected(false);
            addEvent('system', 'Disconnected from server');
        };

        // Detection events
        const handleDetection = (data: DetectionEvent) => {
            addEvent('detection', data.details, data.source, data.frame);
        };

        // Log messages from backend
        const handleLogMessage = (data: LogMessage) => {
            setLogMessages(prev => [...prev.slice(-49), data]); // Keep last 50 messages
            addEvent('log', data.message);
        };

        // Counts updates
        const handleCountsUpdate = (data: CountsUpdate) => {
            setCounts(data);
            addEvent('counts', `Pending: ${data.pending_boxes}, Sold: ${data.boxes_sold}`);
        };

        // Processing status
        const handleProcessingStatus = (data: any) => {
            addEvent('processing', `${data.status}: ${data.message}`, data.source);
        };

        // Processing errors
        const handleProcessingError = (data: any) => {
            addEvent('error', `Error: ${data.message}`, data.source);
        };

        // Zone updates
        const handleZoneUpdate = (data: any) => {
            addEvent('zone', `Zone ${data.zone_id} set to ${data.status}`);
        };

        // GUI reset
        const handleGUIReset = (data: any) => {
            addEvent('system', data.message);
        };

        // Socket event listeners
        socket.on('connect', handleConnect);
        socket.on('disconnect', handleDisconnect);
        socket.on('detection', handleDetection);
        socket.on('log_message', handleLogMessage);
        socket.on('counts_update', handleCountsUpdate);
        socket.on('processing_status', handleProcessingStatus);
        socket.on('processing_error', handleProcessingError);
        socket.on('zone_updated', handleZoneUpdate);
        socket.on('gui_reset', handleGUIReset);

        // Cleanup
        return () => {
            socket.off('connect', handleConnect);
            socket.off('disconnect', handleDisconnect);
            socket.off('detection', handleDetection);
            socket.off('log_message', handleLogMessage);
            socket.off('counts_update', handleCountsUpdate);
            socket.off('processing_status', handleProcessingStatus);
            socket.off('processing_error', handleProcessingError);
            socket.off('zone_updated', handleZoneUpdate);
            socket.off('gui_reset', handleGUIReset);
        };
    }, []);

    const addEvent = (type: string, details: string, source?: string, frame?: number) => {
        const newEvent: DetectionEvent = {
            timestamp: new Date().toISOString(),
            type,
            details,
            source,
            frame
        };
        setEvents(prev => [...prev.slice(-99), newEvent]); // Keep last 100 events
    };

    const getEventIcon = (type: string) => {
        switch (type) {
            case 'detection':
                return '🔍';
            case 'log':
                return '📝';
            case 'counts':
                return '📊';
            case 'processing':
                return '⚙️';
            case 'error':
                return '❌';
            case 'zone':
                return '📍';
            case 'system':
                return '🖥️';
            default:
                return '📋';
        }
    };

    const getEventColor = (type: string) => {
        switch (type) {
            case 'detection':
                return 'text-blue-600';
            case 'log':
                return 'text-gray-600';
            case 'counts':
                return 'text-green-600';
            case 'processing':
                return 'text-purple-600';
            case 'error':
                return 'text-red-600';
            case 'zone':
                return 'text-orange-600';
            case 'system':
                return 'text-gray-800';
            default:
                return 'text-gray-700';
        }
    };

    return (
        <div className="detection-log-card">
            <div className="bg-white rounded-lg shadow-md p-3 flex flex-col" style={{ height: 340 }}>
                <div className="flex justify-between items-center mb-2">
                    <h3 className="text-base font-semibold text-gray-800">Detection Log</h3>
                    <div className="flex items-center space-x-2">
                        <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                        <span className="text-xs text-gray-600">
                            {isConnected ? 'Connected' : 'Disconnected'}
                        </span>
                    </div>
                </div>

                {/* Current Counts Display */}
                {counts && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-2 mb-2">
                        <div className="flex justify-between text-xs">
                            <span className="text-blue-800">
                                <strong>Pending:</strong> {counts.pending_boxes}
                            </span>
                            <span className="text-green-800">
                                <strong>Sold:</strong> {counts.boxes_sold}
                            </span>
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                            Last: {new Date(counts.timestamp).toLocaleTimeString()}
                        </div>
                    </div>
                )}

                {/* Events Log */}
                <div className="detection-log-scroll flex-1 overflow-y-auto space-y-2">
                    {events.length === 0 ? (
                        <div className="text-center text-gray-500 py-4">
                            <div className="text-2xl mb-2">📋</div>
                            <p className="text-xs">No events yet</p>
                            <p className="text-xs">Events will appear here as they occur</p>
                        </div>
                    ) : (
                        events.map((event, index) => (
                            <div
                                key={index}
                                className={`flex items-start space-x-2 p-1 rounded-lg border-l-4 ${event.type === 'error' ? 'border-red-400 bg-red-50' :
                                        event.type === 'detection' ? 'border-blue-400 bg-blue-50' :
                                            event.type === 'counts' ? 'border-green-400 bg-green-50' :
                                                'border-gray-400 bg-gray-50'
                                    }`}
                                style={{ fontSize: '0.95rem' }}
                            >
                                <span className="text-lg">{getEventIcon(event.type)}</span>
                                <div className="flex-1 min-w-0">
                                    <div className={`text-xs font-medium ${getEventColor(event.type)}`}>
                                        {event.details}
                                    </div>
                                    <div className="flex items-center space-x-2 text-xs text-gray-500 mt-1">
                                        <span>{new Date(event.timestamp).toLocaleTimeString()}</span>
                                        {event.source && (
                                            <span className="bg-gray-200 px-1 rounded">Source: {event.source}</span>
                                        )}
                                        {event.frame && (
                                            <span className="bg-gray-200 px-1 rounded">Frame: {event.frame}</span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>

                {/* Clear Log Button */}
                {events.length > 0 && (
                    <button
                        onClick={() => setEvents([])}
                        className="mt-2 px-3 py-1 text-xs text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded transition-colors"
                    >
                        Clear Log
                    </button>
                )}
            </div>
        </div>
    );
};

export default DetectionLog;
