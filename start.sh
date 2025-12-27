#!/bin/bash
PORT=${PORT:-5000}
exec gunicorn backend.run:app --worker-class uviconorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
