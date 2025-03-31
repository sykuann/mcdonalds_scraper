from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from src.database.database import Database
from typing import List, Optional
import logging
from pydantic import BaseModel
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="McDonald's Outlets API",
    description="API for accessing McDonald's outlet information in Malaysia",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Pydantic models for data validation
class OutletBase(BaseModel):
    name: str
    address: str
    telephone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    facilities: List[str] = []
    operating_hours: List[str] = []

class Outlet(OutletBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class OutletSearch(BaseModel):
    query: str
    results: List[Outlet]

class OutletStats(BaseModel):
    total_outlets: int
    outlets_with_coordinates: int
    facilities_count: dict
    outlets_by_state: dict

@app.get("/")
async def root():
    """Root endpoint returning API information."""
    return {
        "name": "McDonald's Outlets API",
        "version": "1.0.0",
        "endpoints": [
            "/outlets",
            "/outlets/{outlet_id}",
            "/search",
            "/stats",
            "/nearby"
        ]
    }

@app.get("/outlets", response_model=List[Outlet])
async def get_outlets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    state: Optional[str] = None
):
    """Get all outlets with optional pagination and state filtering."""
    try:
        db = Database()
        outlets = db.get_all_outlets()
        
        # Apply state filter if provided
        if state:
            outlets = [outlet for outlet in outlets if state.lower() in outlet['address'].lower()]
        
        # Apply pagination
        outlets = outlets[skip:skip + limit]
        
        return outlets
    except Exception as e:
        logger.error(f"Error fetching outlets: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        db.close()

@app.get("/outlets/{outlet_id}", response_model=Outlet)
async def get_outlet(outlet_id: int):
    """Get a specific outlet by ID."""
    try:
        db = Database()
        outlets = db.get_all_outlets()
        outlet = next((outlet for outlet in outlets if outlet['id'] == outlet_id), None)
        
        if not outlet:
            raise HTTPException(status_code=404, detail="Outlet not found")
        
        return outlet
    except Exception as e:
        logger.error(f"Error fetching outlet {outlet_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        db.close()

@app.get("/search", response_model=OutletSearch)
async def search_outlets(query: str):
    """Search outlets by name or address."""
    try:
        db = Database()
        outlets = db.get_all_outlets()
        
        # Perform case-insensitive search
        query = query.lower()
        results = [
            outlet for outlet in outlets
            if query in outlet['name'].lower() or query in outlet['address'].lower()
        ]
        
        return {"query": query, "results": results}
    except Exception as e:
        logger.error(f"Error searching outlets: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        db.close()

@app.get("/stats", response_model=OutletStats)
async def get_stats():
    """Get statistics about the outlets."""
    try:
        db = Database()
        outlets = db.get_all_outlets()
        
        # Calculate statistics
        total_outlets = len(outlets)
        outlets_with_coordinates = sum(1 for outlet in outlets if outlet['latitude'] and outlet['longitude'])
        
        # Count facilities
        facilities_count = {}
        for outlet in outlets:
            for facility in outlet['facilities']:
                facilities_count[facility] = facilities_count.get(facility, 0) + 1
        
        # Count outlets by state (simple implementation)
        outlets_by_state = {}
        for outlet in outlets:
            # Extract state from address (assuming state is mentioned in the address)
            address = outlet['address'].lower()
            if 'kuala lumpur' in address:
                state = 'Kuala Lumpur'
            elif 'selangor' in address:
                state = 'Selangor'
            elif 'johor' in address:
                state = 'Johor'
            else:
                state = 'Other'
            outlets_by_state[state] = outlets_by_state.get(state, 0) + 1
        
        return {
            "total_outlets": total_outlets,
            "outlets_with_coordinates": outlets_with_coordinates,
            "facilities_count": facilities_count,
            "outlets_by_state": outlets_by_state
        }
    except Exception as e:
        logger.error(f"Error calculating statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        db.close()

@app.get("/nearby", response_model=List[Outlet])
async def get_nearby_outlets(
    latitude: float,
    longitude: float,
    radius_km: float = Query(10.0, ge=0.1, le=100.0)
):
    """Get outlets within a specified radius of given coordinates."""
    try:
        db = Database()
        outlets = db.get_all_outlets()
        
        # Filter outlets with coordinates
        outlets_with_coords = [
            outlet for outlet in outlets
            if outlet['latitude'] and outlet['longitude']
        ]
        
        # Calculate distances and filter by radius
        from math import radians, sin, cos, sqrt, atan2
        
        def calculate_distance(lat1, lon1, lat2, lon2):
            R = 6371  # Earth's radius in kilometers
            
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            distance = R * c
            
            return distance
        
        nearby_outlets = []
        for outlet in outlets_with_coords:
            distance = calculate_distance(
                latitude, longitude,
                outlet['latitude'], outlet['longitude']
            )
            if distance <= radius_km:
                outlet['distance_km'] = round(distance, 2)
                nearby_outlets.append(outlet)
        
        # Sort by distance
        nearby_outlets.sort(key=lambda x: x['distance_km'])
        
        return nearby_outlets
    except Exception as e:
        logger.error(f"Error finding nearby outlets: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 