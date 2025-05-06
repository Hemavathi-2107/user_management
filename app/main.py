from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.database import Database
from app.dependencies import get_settings
from app.routers import user_routes
from app.utils.api_description import getDescription

app = FastAPI(
    title="User Management",
    description=getDescription(),
    version="0.0.1",
    contact={
        "name": "API Support",
        "url": "http://www.example.com/support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# 1) CORS middleware must be added before including routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # or ["http://localhost"] for specific
    allow_credentials=True,         # sends Access-Control-Allow-Credentials
    allow_methods=["*"],            # sends Access-Control-Allow-Methods
    allow_headers=["*"],            # sends Access-Control-Allow-Headers
    expose_headers=["*"],           # sends Access-Control-Expose-Headers
    max_age=600,                    # how long preflight can be cached (in seconds)
)

# 2) Application startup: initialize your DB
@app.on_event("startup")
async def startup_event():
    settings = get_settings()
    Database.initialize(settings.database_url, settings.debug)

# 3) Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred."},
    )

# 4) Include your API routes
app.include_router(user_routes.router)
