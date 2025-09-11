from fastapi import FastAPI
from endpoints.ingest_pdf import router as pdf_router

app = FastAPI(title="AgentQI PDF OCR API", version="1.0.0")

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
