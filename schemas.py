"""
Database Schemas for the Business Directory (Κτηνίατροι Ελλάδας)

Each Pydantic model represents a MongoDB collection.
Collection name is the lowercase class name by default.
"""

from pydantic import BaseModel, Field, HttpUrl, conlist, conint
from typing import Optional, List


class Vet(BaseModel):
    """
    Κτηνίατροι (vets) collection schema
    Collection name: "vet"
    """
    name: str = Field(..., description="Επωνυμία ιατρείου ή ονόματεπώνυμο")
    phone: Optional[str] = Field(None, description="Τηλέφωνο επικοινωνίας")
    email: Optional[str] = Field(None, description="Email")
    website: Optional[str] = Field(None, description="Ιστότοπος")
    address: Optional[str] = Field(None, description="Διεύθυνση")
    city: str = Field(..., description="Πόλη")
    region: str = Field(..., description="Περιφέρεια/Νομός")
    latitude: Optional[float] = Field(None, description="Γεωγραφικό πλάτος")
    longitude: Optional[float] = Field(None, description="Γεωγραφικό μήκος")
    specialties: List[str] = Field(default_factory=list, description="Ειδικότητες")
    services: List[str] = Field(default_factory=list, description="Υπηρεσίες")
    hours: Optional[dict] = Field(default=None, description="Ωράριο λειτουργίας")
    rating: float = Field(0.0, ge=0.0, le=5.0, description="Μέση αξιολόγηση")
    reviews_count: int = Field(0, ge=0, description="Πλήθος αξιολογήσεων")
    is_verified: bool = Field(False, description="Επαληθευμένη καταχώρηση")
    avatar_url: Optional[str] = Field(None, description="Εικόνα προφίλ/λογότυπο")


class Review(BaseModel):
    """
    Αξιολογήσεις κτηνιάτρων
    Collection name: "review"
    """
    vet_id: str = Field(..., description="ID κτηνιάτρου")
    author_name: str = Field(..., description="Ονοματεπώνυμο")
    rating: conint(ge=1, le=5) = Field(..., description="Βαθμολογία 1-5")
    comment: Optional[str] = Field(None, description="Σχόλιο")


class User(BaseModel):
    """
    Απλός χρήστης/ιδιοκτήτης καταχώρησης (για μελλοντική χρήση)
    Collection name: "user"
    """
    name: str
    email: str
    avatar_url: Optional[str] = None
    is_active: bool = True
