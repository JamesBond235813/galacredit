#!/usr/bin/env bash

rsync -avz --delete --progress ./backend/ root@120.77.170.193:/www/server/python_project/xhb/xhb_backend \
 --exclude "__MACOSX" --exclude "*/venv" --exclude "tests" --exclude "__pycache__" --exclude ".env.local" --exclude ".env" --exclude "uploads" \
 --exclude "logs" --exclude "pytest.ini" --exclude ".pytest_cache"