from uvicorn import run
from ule.server.api import app
run(app, host='127.0.0.1', port=8000)
