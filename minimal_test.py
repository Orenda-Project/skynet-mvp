"""
Minimal FastAPI app to test Railway deployment.
No database, no models, just a basic endpoint.
"""
from fastapi import FastAPI
import os

app = FastAPI(title="Minimal Test")

@app.get("/")
def root():
    return {
        "message": "Minimal test working!",
        "port": os.getenv("PORT", "not set"),
        "env": os.getenv("ENVIRONMENT", "not set")
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    print(f"Starting minimal test server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
