import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import pandas as pd
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from weather_api.api import app

client = TestClient(app)


def analyze_data():
    """Analyze data to find valid test cases."""
    csv_path = Path(__file__).parent.parent / "weather.csv"
    df = pd.read_csv(csv_path)
    df['event_start'] = pd.to_datetime(df['event_start'])

    # Convert belief horizon to timedelta and calculate belief time
    df['belief_time'] = df.apply(
        lambda row: row['event_start'] - pd.Timedelta(seconds=float(row['belief_horizon_in_sec'])),
        axis=1
    )

    # Print data overview
    logger.info("\nData Overview:")
    logger.info(f"Total records: {len(df)}")
    logger.info(f"Date range: {df['event_start'].min()} to {df['event_start'].max()}")
    logger.info(f"Unique dates: {df['event_start'].dt.date.nunique()}")

    # Find dates with complete forecasts
    date_counts = df.groupby(df['event_start'].dt.date).size()
    consecutive_dates = []

    for i in range(len(date_counts.index) - 1):
        current_date = date_counts.index[i]
        next_date = date_counts.index[i + 1]
        if (next_date - current_date).days == 1:
            # Check if both days have sufficient data
            if date_counts[current_date] >= 3 and date_counts[next_date] >= 3:
                consecutive_dates.append((current_date, next_date))

    if not consecutive_dates:
        raise ValueError("No valid consecutive dates found with complete data")

    # Use the first pair of valid dates
    test_date, next_date = consecutive_dates[0]
    logger.info(f"\nFound consecutive dates: {test_date} -> {next_date}")

    # Get earliest belief time for test date
    test_data = df[df['event_start'].dt.date == test_date]
    earliest_belief = test_data['belief_time'].min()

    logger.info(f"\nFound valid test dates:")
    logger.info(f"Test date: {test_date}")
    logger.info(f"Next date: {next_date}")
    logger.info(f"Earliest belief time: {earliest_belief}")

    return {
        'belief_time': earliest_belief,
        'current_date': test_date,
        'next_date': next_date,
        'records_today': date_counts[test_date],
        'records_tomorrow': date_counts[next_date]
    }


def test_get_forecasts():
    """Test the /forecasts endpoint."""
    data = analyze_data()
    now = data['belief_time'].isoformat()
    then = pd.Timestamp(data['current_date']).isoformat()

    logger.info(f"\nTesting forecasts:")
    logger.info(f"now: {now}")
    logger.info(f"then: {then}")

    response = client.get(
        "/forecasts",
        params={
            "now": now,
            "then": then
        }
    )

    if response.status_code != 200:
        logger.error(f"Error response: {response.json()}")

    assert response.status_code == 200
    result = response.json()
    assert all(key in result for key in ['temperature', 'wind_speed', 'irradiance'])


def test_get_tomorrow_conditions():
    """Test the /tomorrow endpoint."""
    data = analyze_data()
    now = data['belief_time'].isoformat()

    logger.info(f"\nTesting tomorrow conditions:")
    logger.info(f"now: {now}")
    logger.info(f"current_date: {data['current_date']}")
    logger.info(f"tomorrow_date: {data['next_date']}")

    response = client.get(
        "/tomorrow",
        params={
            "now": now
        }
    )

    if response.status_code != 200:
        logger.error(f"Error response: {response.json()}")
        # Print detailed data analysis
        csv_path = Path(__file__).parent.parent / "weather.csv"
        df = pd.read_csv(csv_path)
        df['event_start'] = pd.to_datetime(df['event_start'])
        df['belief_time'] = df.apply(
            lambda row: row['event_start'] - pd.Timedelta(seconds=float(row['belief_horizon_in_sec'])),
            axis=1
        )

        tomorrow_data = df[
            (df['event_start'].dt.date == data['next_date']) &
            (df['belief_time'] <= data['belief_time'])
            ]

        logger.info(f"\nTomorrow data analysis:")
        logger.info(f"Records found: {len(tomorrow_data)}")
        if not tomorrow_data.empty:
            logger.info(f"Sensors: {tomorrow_data['sensor'].unique()}")
            logger.info(f"Forecast times: {tomorrow_data['event_start'].unique()}")

    assert response.status_code == 200
    result = response.json()
    assert all(key in result for key in ['warm', 'sunny', 'windy'])


def test_invalid_datetime():
    """Test invalid datetime format."""
    response = client.get(
        "/forecasts",
        params={
            "now": "invalid-date",
            "then": "2024-02-14T12:00:00"
        }
    )
    assert response.status_code == 422


def test_no_data_available():
    """Test when no data is available."""
    future_date = "2025-01-01T00:00:00Z"
    response = client.get(
        "/forecasts",
        params={
            "now": future_date,
            "then": future_date
        }
    )
    assert response.status_code == 404
    assert "No forecasts available" in response.json()["detail"]


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


if __name__ == "__main__":
    # Run data analysis directly
    data = analyze_data()
    logger.info("\nTest data values:")
    for key, value in data.items():
        logger.info(f"{key}: {value}")