import React, { useState, useEffect } from 'react';

interface ZoneSelectorProps {
    onSelect: (zoneId: string) => void;
}

const ZoneSelector: React.FC<ZoneSelectorProps> = ({ onSelect }) => {
    const [zones, setZones] = useState<string[]>([]);
    const [selectedZone, setSelectedZone] = useState<string>('');

    useEffect(() => {
        // Fetch available zones from the backend
        const fetchZones = async () => {
            try {
                const response = await fetch('http://localhost:5000/api/zones');
                const data = await response.json();
                setZones(data.zones);
            } catch (error) {
                console.error('Error fetching zones:', error);
            }
        };

        fetchZones();
    }, []);

    const handleZoneChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const zoneId = event.target.value;
        setSelectedZone(zoneId);
        onSelect(zoneId);
    };

    return (
        <div className="component-card">
            <h3>Detection Zone</h3>
            <select value={selectedZone} onChange={handleZoneChange}>
                <option value="">Select a zone</option>
                {zones.map((zone) => (
                    <option key={zone} value={zone}>
                        Zone {zone}
                    </option>
                ))}
            </select>
        </div>
    );
};

export default ZoneSelector;
