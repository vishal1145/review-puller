from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class Reviewer(BaseModel):
    profile_photo_url: str
    display_name: str
    link: str

class Review(BaseModel):
    review_id: str = Field(..., description="Unique review ID")
    place_id: str = Field(..., description="Associated Google Place ID")
    place_name: Optional[str] = None
    reviewer: Reviewer
    link: str
    source: str = "Google"
    source_logo: str = "https://www.gstatic.com/images/branding/product/1x/googleg_48dp.png"
    rating: str
    created: str
    date: str
    comment: Optional[str] = None
    photos: List[str] = Field(default_factory=list)
    checked: bool = Field(default=False, description="Flag for processing status")
    ai_response: bool = Field(default=False, description="Indicates if AI has processed the review")  

    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 