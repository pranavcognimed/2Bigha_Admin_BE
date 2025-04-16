import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from routers import properties, auth,users
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env
load_dotenv()

# Add the base directory to sys.path
BASE_DIR = os.getenv("PYTHONPATH", ".")
sys.path.append(BASE_DIR)

app = FastAPI(title="Real Estate Admin API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(properties.router, prefix="/properties")
app.include_router(auth.router, prefix="/auth")
app.include_router(users.router, prefix="/users")

# Start your FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)