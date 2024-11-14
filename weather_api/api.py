from fastapi import FastAPI, Query, HTTPException
from datetime import datetime
from typing import Dict, Optional
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

from .data_handler import WeatherDataHandler

app = FastAPI(
    title="Weather Forecast API",
    description="API for retrieving weather forecasts and conditions",
    version="1.0.0"
)

def get_weather_data():
    """Initialize weather data handler."""
    try:
        data_path = Path(__file__).parent.parent / "weather.csv"
        if not data_path.exists():
            raise FileNotFoundError(f"Weather data file not found at {data_path}")
        return WeatherDataHandler(str(data_path))
    except Exception as e:
        raise RuntimeError(f"Failed to initialize weather data: {str(e)}")

# Initialize data handler
weather_data = get_weather_data()

@app.get("/forecasts")
async def get_forecasts(
    now: datetime = Query(..., description="Current datetime (ISO format)"),
    then: datetime = Query(..., description="Target forecast datetime (ISO format)")
) -> Dict[str, Optional[float]]:
    """Get forecasts for a specific time."""
    try:
        logger.info(f"Getting forecasts - now: {now}, then: {then}")
        return weather_data.get_forecasts(now, then)
    except ValueError as e:
        logger.warning(f"No forecasts available: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting forecasts: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tomorrow")
async def get_tomorrow_conditions(
    now: datetime = Query(..., description="Current datetime (ISO format)")
) -> Dict[str, bool]:
    """Get tomorrow's weather conditions."""
    try:
        logger.info(f"Getting tomorrow's conditions - now: {now}")
        return weather_data.get_tomorrow_conditions(now)
    except ValueError as e:
        logger.warning(f"No forecasts available: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting tomorrow's conditions: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "API is running"}