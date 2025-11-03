#!/bin/sh
python ./src/matcher.py &
fastapi run ./src/main.py