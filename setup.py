from setuptools import setup, find_packages

setup(
    name="neurospace",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn==0.24.0",
        "python-multipart==0.0.6",
        "sqlalchemy==2.0.23",
        "psycopg2-binary==2.9.9",
        "python-dotenv==1.0.0",
        "openai==1.3.5",
        "web3==6.11.1",
        "ipfshttpclient==0.8.0",
        "pgvector==0.2.3",
        "PyPDF2==3.0.1",
        "redis>=4.5.1",
        "pytest>=7.0.0",
        "httpx>=0.24.0",
        "eth-typing<3.0.0",
        "eth-account<0.10.0",
        "eth-utils<3.0.0"
    ],
) 