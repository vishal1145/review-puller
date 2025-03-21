from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field

class Place(BaseModel):
    place_id: str = Field(..., description="Unique Google Place ID")
    name: str = Field(..., description="Name of the place")
    location_name: str

    address: Optional[str] = Field(None, description="Address of the place")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    rating: Optional[float] = Field(None, description="Average rating")
    total_ratings: Optional[int] = Field(None, description="Total number of ratings")
    scraped: bool = Field(default=False, description="Flag for tracking if reviews have been scraped")
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 