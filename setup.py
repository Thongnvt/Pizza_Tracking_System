from setuptools import setup, find_packages

setup(
    name="counting-system",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'flask==2.0.1',
        'flask-cors==3.0.10',
        'flask-socketio==5.1.1',
        'numpy==1.21.0',
        'opencv-python==4.5.3.56',
        'filterpy==1.4.5',
        'lap==0.4.0',
        'shapely==1.8.0',
        'ultralytics==8.0.0',
        'torch==1.9.0',
        'torchvision==0.10.0',
        'python-socketio==5.4.0',
        'python-engineio==4.2.1',
    ],
) 