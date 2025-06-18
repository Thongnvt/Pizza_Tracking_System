import numpy as np
import cv2
from shapely.geometry import Polygon, Point

class DispatchZone:
    def __init__(self, coordinates, name="Unnamed Zone"):
        """
        Initialize a dispatch zone with coordinates and name
        
        Args:
            coordinates (list): List of (x, y) coordinates defining the zone polygon
            name (str): Name of the zone
        """
        self.coordinates = np.array(coordinates, dtype=np.int32)
        self.name = name
        self.color = (0, 255, 0)  # Default color (green)
        self.thickness = 2
        
        # Initialize polygon for area calculations
        self.polygon = Polygon(coordinates)
        
        # Calculate center point
        self.center = np.mean(self.coordinates, axis=0)
        
    def is_point_inside(self, point):
        """
        Check if a point is inside the zone
        
        Args:
            point (tuple): (x, y) coordinates of the point
            
        Returns:
            bool: True if point is inside zone, False otherwise
        """
        return self.polygon.contains(Point(point))
        
    def get_center(self):
        """Get the center point of the zone"""
        return self.center
        
    def set_color(self, color):
        """Set the zone's color"""
        self.color = color
        
    def set_thickness(self, thickness):
        """Set the zone's line thickness"""
        self.thickness = thickness
        
    def get_area_size(self):
        """Get the area of the zone in square pixels"""
        return self.polygon.area
        
    def to_dict(self):
        """Convert zone to dictionary representation"""
        return {
            'name': self.name,
            'coordinates': self.coordinates.tolist(),
            'color': self.color,
            'thickness': self.thickness
        }
        
    @classmethod
    def from_dict(cls, data):
        """Create a DispatchZone instance from dictionary"""
        zone = cls(data['coordinates'], data['name'])
        zone.color = tuple(data['color'])
        zone.thickness = data['thickness']
        return zone

    def _calculate_sub_areas(self):
        """Calculate the 4 sub-areas by dividing the polygon"""
        
        center_x, center_y = self.get_center()
        
        
        sub_areas = []
        for i in range(4):
            
            p1 = self.coordinates[i]
            p2 = self.coordinates[(i + 1) % 4]
            

            sub_polygon = Polygon([p1, p2, [center_x, center_y]])
            sub_areas.append(sub_polygon)
            
        return sub_areas
    
    def draw_zone(self, frame):
        """Draw the dispatch zone and its sub-areas on the frame"""
        
        cv2.polylines(frame, [self.coordinates], True, (255, 0, 255), 2)
        
        
        cv2.circle(frame, (int(self.get_center()[0]), int(self.get_center()[1])), 5, (0, 0, 255), -1)
        
        
        for point in self.coordinates:
            cv2.line(frame, 
                    (int(self.get_center()[0]), int(self.get_center()[1])),
                    (int(point[0]), int(point[1])),
                    (255, 0, 255), 1)
        
        
        text_size = cv2.getTextSize(self.name, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        text_x = int(self.get_center()[0] - text_size[0] // 2)
        text_y = int(min(self.coordinates[:, 1])) - 10
        cv2.putText(frame, self.name, (text_x, text_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        
        for i, sub_area in enumerate(self._calculate_sub_areas()):
            # Calculate centroid of sub-area for label placement
            centroid = sub_area.centroid
            cv2.putText(frame, f"Area {i+1}", 
                       (int(centroid.x), int(centroid.y)),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def is_point_in_zone(self, point):
        """Check if a point is inside the dispatch zone"""
        return self.is_point_inside(point)
    
    def get_sub_area(self, point):
        """Get the sub-area number (1-4) that contains the point"""
        if not self.is_point_in_zone(point):
            return None
            
        for i, sub_area in enumerate(self._calculate_sub_areas()):
            if sub_area.contains(Point(point)):
                return i + 1
        return None
    
    def get_sub_area_sizes(self):
        """Get the areas of all sub-areas in square pixels"""
        return [area.area for area in self._calculate_sub_areas()]


