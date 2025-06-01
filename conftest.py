# conftest.py in root dir
import pytest

def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: mark test to run with asyncio")