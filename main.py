from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers.auth_oidc import router as auth_router
import os

app = FastAPI()

app.include_router(auth_router)

app.mount("/static", StaticFiles(directory="static", html=True), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def serve_home():
    return FileResponse("static/Home.html")

from routes import (
    auth_routes,
    property_routes,
    product_routes,
    ops_routes,
    report_routes,
    misc_routes,
    equipment_routes
)

app.include_router(auth_routes.router)
app.include_router(property_routes.router)
app.include_router(product_routes.router)
app.include_router(ops_routes.router)
app.include_router(report_routes.router)
app.include_router(misc_routes.router)
app.include_router(equipment_routes.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False) # change for server hose 0.0.0.0 port 8080


