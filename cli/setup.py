from setuptools import setup, find_packages

setup(
    name="unweb",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click",
        "httpx",
        "rich",
    ],
    entry_points={
        "console_scripts": [
            "unweb=unweb.cli:main",
        ],
    },
    python_requires=">=3.9",
)
