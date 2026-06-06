from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.analytics import get_rfm_data


app = FastAPI(
    title="CRM Analytics API",
    description="Backend API për analizën dhe segmentimin e klientëve SME.",
    version="1.0.0"
)


# CORS configuration
# For development we allow all origins. In production this should be restricted.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "status": "online",
        "message": "CRM Analytics API is running",
        "project": "Customer segmentation using RFM and K-Means"
    }


@app.get("/api/rfm-data")
def rfm_data():
    try:
        result = get_rfm_data()

        return {
            "status": "success",
            "total_customers": len(result),
            "data": result.to_dict(orient="records")
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not process RFM data: {error}"
        )