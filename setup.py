from setuptools import setup, find_packages

setup(
    name='classifier',
    version='0.1.0',
    author='Bonnie Gachiengu',
    author_email='bonniegachiengu@gmail.com',
    description='A media management application for metadata collection, file indexing, and content analysis.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/bonniegachiengu/classifier',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    install_requires=[
        # List your package dependencies here
    ],
)