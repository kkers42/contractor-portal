from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()

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
    misc_routes
)

app.include_router(auth_routes.router)
app.include_router(property_routes.router)
app.include_router(product_routes.router)
app.include_router(ops_routes.router)
app.include_router(report_routes.router)
app.include_router(misc_routes.router)

if __name__ == "__main__":
    import uvicorn
    print("🔥 Uvicorn is starting...")
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
