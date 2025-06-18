from filterpy.kalman import KalmanFilter
import numpy as np

def xyxy_to_cxcywh(bbox):
    x1, y1, x2, y2 = bbox
    w, h = x2 - x1, y2 - y1
    cx, cy = x1 + w / 2., y1 + h / 2.
    return np.array([cx, cy, w, h])

def cxcywh_to_xyxy(state):
    cx, cy, w, h = state[:4].flatten()
    w, h = max(w, 1e-2), max(h, 1e-2)  
    x1, y1, x2, y2 = cx - w / 2., cy - h / 2., cx + w / 2., cy + h / 2.
    return np.array([x1, y1, x2, y2])

class KalmanBox:
    def __init__(self, bbox):
        # x, y, s, r: center x/y, scale (area), aspect ratio
        self.kf = KalmanFilter(dim_x=7, dim_z=4)
        self.kf.F = np.array([
            [1, 0, 0, 0, 1, 0, 0],
            [0, 1, 0, 0, 0, 1, 0],
            [0, 0, 1, 0, 0, 0, 1],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 1]
        ])
        self.kf.H = np.array([
            [1, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0]
        ])
        self.kf.R[2:, 2:] *= 10.  
        self.kf.P[4:, 4:] *= 1000. 
        self.kf.Q[4:, 4:] *= 0.01

        self.kf.x[:4] = xyxy_to_cxcywh(bbox).reshape((4,1))

    def predict(self):
        self.kf.predict()
        return cxcywh_to_xyxy(self.kf.x)

    def update(self, bbox):
        self.kf.update(xyxy_to_cxcywh(bbox))
