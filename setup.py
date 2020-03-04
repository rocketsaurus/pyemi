from distutils.core import setup
setup(
    name = 'pyemi',
    packages = ['pyemi'],
    package_dir = {'pyemi': ''},
    package_data = {'pyemi': ['drivers/*.yaml']},
    version = '0.8',
    license='MIT',
    description = 'Instrument drivers for EMC regulatory related tests and automation.',
    author = 'Jeremy Chinn',
    author_email = 'jeremychinn88@gmail.com', 
    url = 'https://github.com/rocketsaurus/pyemi', 
    download_url = 'https://github.com/rocketsaurus/pyemi/archive/v0.8-alpha.tar.gz', 
    keywords = ['EMC', 'drivers', 'spectrum', 'analyzer', 'signal', 'generator'], 
    install_requires=[ 
        'numpy',
        'pandas',
        'ruamel.yaml',
        'pyvisa'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        'Intended Audience :: Developers',      # Define that your audience are developers
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License', 
        'Programming Language :: Python :: 3', 
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)