import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
backend_dir = os.path.join(root_dir, "backend")

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from backend.main import app
from backend.database import connect_db, db_client, InMemoryDatabase

@app.middleware("http")
async def ensure_db_connected(request, call_next):
    if db_client.db is None:
        try:
            await connect_db()
        except Exception:
            db_client.db = InMemoryDatabase()
            db_client.is_mock = True
    response = await call_next(request)
    return response
