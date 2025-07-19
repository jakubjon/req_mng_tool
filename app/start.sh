#!/bin/sh
set -e
python -m db_mng.init_db
exec python app.py
