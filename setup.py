from setuptools import setup, find_packages

setup(
    name="neurochain",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.109.2",
        "uvicorn==0.27.1",
        "python-dotenv==1.0.1",
        "web3==6.11.1",
        "eth-typing==4.0.0",
        "ipfshttpclient>=0.8.0a2",
        "pydantic==2.6.1",
        "pydantic-settings==2.1.0",
        "python-multipart==0.0.9",
        "transformers==4.37.2",
        "torch==2.2.0",
        "accelerate==0.27.2",
    ],
    extras_require={
        "test": [
            "pytest==7.4.3",
            "pytest-asyncio==0.21.1",
            "pytest-cov==4.1.0",
            "httpx==0.25.2",
        ],
    },
) 