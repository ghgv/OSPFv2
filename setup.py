from setuptools import setup, find_packages

setup(
    name="ospf_daemon",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "dash",
        "dash-cytoscape",
        "networkx",
        "matplotlib"
    ],
    entry_points={
        'console_scripts': [
            'ospf-daemon = ospf_daemon.__main__:main'
        ]
    },
    author="Tu Nombre",
    description="Daemon OSPFv2 educativo en Python con visualización en tiempo real",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
        "Topic :: System :: Networking"
    ],
    python_requires='>=3.7',
)
