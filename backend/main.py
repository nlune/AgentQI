from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from endpoints.ingest_pdf import router as pdf_router
import os

app = FastAPI(title="AgentQI PDF OCR API", version="1.0.0")

# Ensure storage directories exist
os.makedirs(os.path.join("storage", "original_pdfs"), exist_ok=True)
os.makedirs(os.path.join("storage", "annotated_pdfs"), exist_ok=True)

# Mount static file serving for PDFs
app.mount("/pdfs/original", StaticFiles(directory=os.path.join("storage", "original_pdfs")), name="original_pdfs")
app.mount("/pdfs/annotated", StaticFiles(directory=os.path.join("storage", "annotated_pdfs")), name="annotated_pdfs")

# Include routers
app.include_router(pdf_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to AgentQI PDF OCR API"}

def main():
    print("Hello from backend!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
