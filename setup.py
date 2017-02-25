from setuptools import find_packages, setup

setup(
    name='grid_generator',
    version='1.0.0',
    packages=find_packages(exclude=["*.tests", "tests"]),
    package_data={'': ['']},
    install_requires=[
        'shapely',
        'functions32==3.2.3.post2',
        'geojson==1.3.2',
        'pyproj==1.9.5.1'
    ],
    description='Python library containing logic to generate grid 5x5 meters'
)
