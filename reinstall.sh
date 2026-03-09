#!/bin/bash
cd "$(dirname "$0")"
rm -rf build/ dist/ *.egg-info/
python setup.py bdist_wheel
pip uninstall -y ib_strategies 2>/dev/null || true
pip install dist/*.whl && echo "Installation successful!"
