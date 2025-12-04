#/bin/bash
# Converts scripts to Unix line endings (LF)
# Use this when building / using the Docker container on WSL / Linux
find . -type f -print0 | xargs -0 dos2unix