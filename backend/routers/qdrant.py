from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union
from qdrant_client import QdrantClient
from qdrant_client.http import models

router = APIRouter(
    prefix="/qdrant",
    tags=["qdrant"],
    responses={404: {"description": "Not found"}},
)

# Initialize Qdrant Client
# Connect to the self-hosted Qdrant instance
client = QdrantClient(host="localhost", port=6333)

class PointData(BaseModel):
    id: Union[int, str]
    vector: List[float]
    payload: Optional[Dict[str, Any]] = None

class UpsertRequest(BaseModel):
    collection_name: str
    points: List[PointData]

class SearchRequest(BaseModel):
    collection_name: str
    vector: List[float]
    limit: int = 10
    score_threshold: Optional[float] = None

@router.post("/upsert")
async def upsert_points(request: UpsertRequest):
    """
    Upsert points into a collection.
    Supports bulk update as 'points' is a list.
    """
    try:
        # Check if collection exists, if not create it with default config (vector size inferred from first point?)
        # For simplicity, we assume collection exists or user creates it. 
        # But to be helpful, let's check and create if missing, assuming a vector size.
        # However, we don't know the vector size if we just create it blindly. 
        # So we will let it fail if collection doesn't exist, or user can use a separate setup endpoint.
        # Actually, let's just try to upsert.
        
        points_list = [
            models.PointStruct(
                id=p.id,
                vector=p.vector,
                payload=p.payload
            ) for p in request.points
        ]
        
        operation_info = client.upsert(
            collection_name=request.collection_name,
            points=points_list
        )
        return {"status": "success", "operation_info": operation_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search_points(request: SearchRequest):
    """
    Search for nearest vectors in a collection.
    """
    try:
        search_result = client.search(
            collection_name=request.collection_name,
            query_vector=request.vector,
            limit=request.limit,
            score_threshold=request.score_threshold
        )
        return {"result": search_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create_collection")
async def create_collection(collection_name: str, vector_size: int, distance: str = "Cosine"):
    """
    Helper endpoint to create a collection since upsert requires it.
    """
    try:
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance[distance.upper()])
        )
        return {"status": "success", "message": f"Collection {collection_name} created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
