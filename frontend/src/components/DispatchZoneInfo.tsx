import React, { useState, useEffect } from 'react';

interface DispatchZoneInfoProps {
    selectedZone: number | null;
    onZoneSelect: (zoneId: number) => void;
}

interface ZoneInfo {
    id: number;
    name: string;
    count: number;
    alerts: Array<{
        type: string;
        message: string;
    }>;
}

const DispatchZoneInfo: React.FC<DispatchZoneInfoProps> = ({ selectedZone, onZoneSelect }) => {
    const [zoneInfo, setZoneInfo] = useState<ZoneInfo | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchZoneInfo = async () => {
            if (!selectedZone) return;

            try {
                setIsLoading(true);
                setError(null);
                const response = await fetch(`http://localhost:5000/api/zone-info`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                // Find the zone info for the selected zone
                const zoneData = data.find((zone: any) => zone.zoneId === selectedZone.toString());
                if (zoneData) {
                    setZoneInfo({
                        id: parseInt(zoneData.zoneId),
                        name: `Zone ${zoneData.zoneId}`,
                        count: zoneData.count,
                        alerts: [{
                            type: zoneData.status === 'active' ? 'info' : 'warning',
                            message: `Status: ${zoneData.status}`
                        }]
                    });
                } else {
                    throw new Error('Zone not found');
                }
            } catch (error) {
                console.error('Error fetching zone info:', error);
                setError('Failed to load zone information');
                setZoneInfo(null);
            } finally {
                setIsLoading(false);
            }
        };

        fetchZoneInfo();
    }, [selectedZone]);

    const handleZoneSelect = async (zoneId: number) => {
        try {
            // Call the set-zone endpoint to update the active zone on the backend
            const response = await fetch('http://localhost:5000/api/set-zone', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ zone_id: zoneId }),
            });

            if (!response.ok) {
                throw new Error(`Failed to set zone: ${response.status}`);
            }

            // Call the parent callback
            onZoneSelect(zoneId);
        } catch (error) {
            console.error('Error setting zone:', error);
            // Still call the parent callback even if the API call fails
            onZoneSelect(zoneId);
        }
    };

    return (
        <div className="component-card">
            <h3>Zone Information</h3>
            <div className="zone-selector">
                {[1, 2, 3, 4, 5, 6].map((zoneId) => (
                    <button
                        key={zoneId}
                        className={`zone-button ${selectedZone === zoneId ? 'selected' : ''}`}
                        onClick={() => handleZoneSelect(zoneId)}
                    >
                        Zone {zoneId}
                    </button>
                ))}
            </div>

            {isLoading ? (
                <div className="loading">Loading zone information...</div>
            ) : error ? (
                <div className="error">{error}</div>
            ) : zoneInfo ? (
                <div className="zone-info">
                    <div className="zone-header">
                        <h4>{zoneInfo.name}</h4>
                        <span className="count">Count: {zoneInfo.count}</span>
                    </div>
                    <div className="alerts">
                        {zoneInfo.alerts.map((alert, index) => (
                            <div key={index} className={`alert ${alert.type}`}>
                                {alert.message}
                            </div>
                        ))}
                    </div>
                </div>
            ) : (
                <div className="no-zone-message">
                    Select a zone to view information
                </div>
            )}
        </div>
    );
};

export default DispatchZoneInfo;
