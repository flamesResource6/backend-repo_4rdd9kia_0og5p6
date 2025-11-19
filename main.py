import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Vet, Review

app = FastAPI(title="Greek Vets Directory API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class VetPublic(BaseModel):
    id: str
    name: str
    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]
    address: Optional[str]
    city: str
    region: str
    latitude: Optional[float]
    longitude: Optional[float]
    specialties: List[str]
    services: List[str]
    hours: Optional[dict]
    rating: float
    reviews_count: int
    is_verified: bool
    avatar_url: Optional[str]


@app.get("/")
def root():
    return {"message": "Greek Vets Directory API ready"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "Unknown"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


@app.post("/api/vets", response_model=str)
def create_vet(vet: Vet):
    vet_id = create_document("vet", vet)
    return vet_id


@app.get("/api/vets", response_model=List[VetPublic])
def list_vets(city: Optional[str] = None, region: Optional[str] = None, q: Optional[str] = None, limit: int = 50):
    filter_dict = {}
    if city:
        filter_dict["city"] = {"$regex": city, "$options": "i"}
    if region:
        filter_dict["region"] = {"$regex": region, "$options": "i"}
    if q:
        # Search in name, services, specialties, city
        filter_dict["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"services": {"$elemMatch": {"$regex": q, "$options": "i"}}},
            {"specialties": {"$elemMatch": {"$regex": q, "$options": "i"}}},
            {"city": {"$regex": q, "$options": "i"}},
        ]

    docs = get_documents("vet", filter_dict, limit)

    def map_doc(d):
        return VetPublic(
            id=str(d.get("_id")),
            name=d.get("name"),
            phone=d.get("phone"),
            email=d.get("email"),
            website=d.get("website"),
            address=d.get("address"),
            city=d.get("city"),
            region=d.get("region"),
            latitude=d.get("latitude"),
            longitude=d.get("longitude"),
            specialties=d.get("specialties", []),
            services=d.get("services", []),
            hours=d.get("hours"),
            rating=float(d.get("rating", 0.0)),
            reviews_count=int(d.get("reviews_count", 0)),
            is_verified=bool(d.get("is_verified", False)),
            avatar_url=d.get("avatar_url"),
        )

    return [map_doc(d) for d in docs]


@app.get("/api/vets/{vet_id}", response_model=VetPublic)
def get_vet(vet_id: str):
    try:
        doc = db.vet.find_one({"_id": ObjectId(vet_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid vet id")
    if not doc:
        raise HTTPException(status_code=404, detail="Vet not found")
    return VetPublic(
        id=str(doc.get("_id")),
        name=doc.get("name"),
        phone=doc.get("phone"),
        email=doc.get("email"),
        website=doc.get("website"),
        address=doc.get("address"),
        city=doc.get("city"),
        region=doc.get("region"),
        latitude=doc.get("latitude"),
        longitude=doc.get("longitude"),
        specialties=doc.get("specialties", []),
        services=doc.get("services", []),
        hours=doc.get("hours"),
        rating=float(doc.get("rating", 0.0)),
        reviews_count=int(doc.get("reviews_count", 0)),
        is_verified=bool(doc.get("is_verified", False)),
        avatar_url=doc.get("avatar_url"),
    )


class ReviewPublic(BaseModel):
    id: str
    vet_id: str
    author_name: str
    rating: int
    comment: Optional[str]


@app.post("/api/reviews", response_model=str)
def create_review(review: Review):
    # Aggregate rating and count for vet
    vet_id = review.vet_id
    create_id = create_document("review", review)
    try:
        pipeline = [
            {"$match": {"vet_id": vet_id}},
            {"$group": {"_id": "$vet_id", "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}}
        ]
        stats = list(db.review.aggregate(pipeline))
        if stats:
            s = stats[0]
            db.vet.update_one({"_id": ObjectId(vet_id)}, {"$set": {"rating": float(s.get("avg", 0)), "reviews_count": int(s.get("count", 0))}})
    except Exception:
        pass
    return create_id


@app.get("/api/vets/{vet_id}/reviews", response_model=List[ReviewPublic])
def list_reviews(vet_id: str, limit: int = 50):
    docs = get_documents("review", {"vet_id": vet_id}, limit)
    return [
        ReviewPublic(
            id=str(d.get("_id")),
            vet_id=d.get("vet_id"),
            author_name=d.get("author_name"),
            rating=int(d.get("rating", 0)),
            comment=d.get("comment")
        ) for d in docs
    ]


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
