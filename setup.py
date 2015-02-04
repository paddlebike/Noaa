from distutils.core import setup

setup(
    name='Noaa',
    version='1.0.0',
    author='Ken Andrews',
    author_email='surfnk1@aol.com',
    packages=['noaa'],
    license='LICENSE.txt',
    description='Get weather and river level information',
    long_description=open('README.txt').read(),
    install_requires=[
    ],
)
