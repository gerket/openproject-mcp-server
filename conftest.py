"""Pytest configuration: set required environment variables for all test modules."""

import os

# Set before any src.* imports so OpenProjectClient initialises without error.
os.environ.setdefault("OPENPROJECT_URL", "http://test.example.com")
os.environ.setdefault("OPENPROJECT_API_KEY", "test-key")
