"""Pytest configuration: set required environment variables for all test modules."""

import os

# Set before any src.* imports so OpenProjectClient initialises without error.
os.environ.setdefault("OPENPROJECT_URL", "http://test.example.com")
os.environ.setdefault("OPENPROJECT_API_KEY", "test-key")

# src.server reads these at import time and applies tag filtering globally for
# the whole run. Clear them here — before any src.* import — so a developer who
# has tag filters set in their own environment gets the full, unfiltered tool
# set the unit tests assert against. (Only affects this pytest process.)
os.environ.pop("OPENPROJECT_MCP_INCLUDE_TAGS", None)
os.environ.pop("OPENPROJECT_MCP_EXCLUDE_TAGS", None)
