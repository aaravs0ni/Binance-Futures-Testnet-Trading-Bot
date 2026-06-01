"""
Pytest configuration file.
Sets up fixtures and configuration for all tests.
"""

import sys
from pathlib import Path

# Add parent directory to path so bot module can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))
