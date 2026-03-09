"""
Setup script for ib_trading package.
"""

from pathlib import Path
from setuptools import setup, find_packages


# Read requirements from requirements.txt
def read_requirements():
    """Read requirements from requirements.txt file."""
    requirements_file = Path(__file__).parent / "requirements.txt"
    if requirements_file.exists():
        with open(requirements_file, 'r', encoding='utf-8') as f:
            return [
                line.strip()
                for line in f
                if line.strip() and not line.startswith('#')
            ]
    return []


setup(
    name="ib_strategies",
    version="0.1.0",
    author="Qimian Xian",
    description="Python library for Interactive Brokers trading via Client Portal Gateway REST API",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=read_requirements(),
)