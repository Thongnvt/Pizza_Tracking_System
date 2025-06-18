import React, { useEffect, useState } from 'react';
import { socket } from '../socket';

interface Statistics {
    total_detections: number;
    current_session: number;
    boxes_sold: number;
    pending_boxes: number;
    open_boxes_in_zone: number;
    closed_boxes_in_zone: number;
}

const BoxStatistics: React.FC = () => {
    const [statistics, setStatistics] = useState<Statistics>({
        total_detections: 0,
        current_session: 0,
        boxes_sold: 0,
        pending_boxes: 0,
        open_boxes_in_zone: 0,
        closed_boxes_in_zone: 0
    });
    const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

    useEffect(() => {
        // Fetch initial statistics
        fetchStatistics();

        // Listen for real-time statistics updates
        const handleStatisticsUpdate = (data: Statistics) => {
            setStatistics(data);
            setLastUpdate(new Date());
        };

        socket.on('statistics_update', handleStatisticsUpdate);

        // Cleanup
        return () => {
            socket.off('statistics_update', handleStatisticsUpdate);
        };
    }, []);

    const fetchStatistics = async () => {
        try {
            const response = await fetch('http://localhost:5000/api/statistics');
            if (response.ok) {
                const data = await response.json();
                if (data.status === 'success') {
                    setStatistics({
                        total_detections: data.total || 0,
                        current_session: data.current || 0,
                        boxes_sold: data.boxes_sold || 0,
                        pending_boxes: data.pending_boxes || 0,
                        open_boxes_in_zone: data.open_boxes_in_zone || 0,
                        closed_boxes_in_zone: data.closed_boxes_in_zone || 0
                    });
                    setLastUpdate(new Date());
                }
            }
        } catch (error) {
            console.error('Error fetching statistics:', error);
        }
    };

    const StatCard: React.FC<{ title: string; value: number; color: string; icon: string }> = ({
        title,
        value,
        color,
        icon
    }) => (
        <div className={`bg-white rounded-lg shadow-md p-4 border-l-4 ${color}`}>
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-sm font-medium text-gray-600">{title}</p>
                    <p className="text-2xl font-bold text-gray-900">{value}</p>
                </div>
                <div className="text-2xl">{icon}</div>
            </div>
        </div>
    );

    return (
        <div className="bg-white rounded-lg shadow-md p-4">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-800">Box Statistics</h3>
                <button
                    onClick={fetchStatistics}
                    className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                >
                    Refresh
                </button>
            </div>

            {/* Last Update Info */}
            {lastUpdate && (
                <div className="text-xs text-gray-500 mb-4">
                    Last updated: {lastUpdate.toLocaleTimeString()}
                </div>
            )}

            {/* Statistics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <StatCard
                    title="Boxes Sold"
                    value={statistics.boxes_sold}
                    color="border-green-500"
                    icon="📦"
                />
                <StatCard
                    title="Pending Boxes"
                    value={statistics.pending_boxes}
                    color="border-yellow-500"
                    icon="⏳"
                />
                <StatCard
                    title="Open in Zone"
                    value={statistics.open_boxes_in_zone}
                    color="border-blue-500"
                    icon="📂"
                />
                <StatCard
                    title="Closed in Zone"
                    value={statistics.closed_boxes_in_zone}
                    color="border-red-500"
                    icon="📁"
                />
                <StatCard
                    title="Total Detections"
                    value={statistics.total_detections}
                    color="border-purple-500"
                    icon="🔍"
                />
                <StatCard
                    title="Current Session"
                    value={statistics.current_session}
                    color="border-indigo-500"
                    icon="🎯"
                />
            </div>

            {/* Summary */}
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Summary</h4>
                <div className="text-sm text-gray-600 space-y-1">
                    <p>• Total boxes processed: {statistics.total_detections}</p>
                    <p>• Successfully sold: {statistics.boxes_sold}</p>
                    <p>• Currently in dispatch zone: {statistics.open_boxes_in_zone + statistics.closed_boxes_in_zone}</p>
                    <p>• Awaiting processing: {statistics.pending_boxes}</p>
                </div>
            </div>
        </div>
    );
};

export default BoxStatistics;
