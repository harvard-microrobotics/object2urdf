from setuptools import setup, find_packages

setup(
    name='object2urdf',
    version='0.13',
    packages=find_packages(exclude=['tests*']),
    license='MIT',
    description='Manage URDF files for a library of objects',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=['numpy', 'scipy', 'trimesh', 'pillow', 'networkx'],
    url='https://github.com/cbteeple/object2urdf',
    author='Clark Teeple',
    author_email='cbteeple@gmail.com',
)