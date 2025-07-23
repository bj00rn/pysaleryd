#!/bin/bash
set -e

# Mark workspace as a safe git directory
git config --global --add safe.directory .

# Upgrade pip
pip install --upgrade pip

# Install documentation requirements
pip install -r docs/requirements.txt

# Install project in editable mode with testing extras
pip install -e .[testing]
