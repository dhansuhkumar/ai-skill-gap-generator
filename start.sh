#!/bin/bash
PORT=${PORT:-5000}
exec gunicorn backend.run:app --bind 0.0.0.0:$PORT