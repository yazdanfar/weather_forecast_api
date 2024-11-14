# Weather Forecast API

This API provides weather forecast information through two endpoints:
- `/forecasts`: Get forecasts for a specific time based on knowledge available at a given moment
- `/tomorrow`: Get boolean indicators for tomorrow's weather conditions

## Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd weather-api
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the API:
```bash
uvicorn weather_api.api:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

### GET /forecasts
Get forecasts for a specific time based on knowledge available at a given moment.

Parameters:
- `now`: ISO datetime string (e.g., "2024-02-14T12:00:00")
- `then`: ISO datetime string (e.g., "2024-02-14T15:00:00")

Example:
```
GET /forecasts?now=2024-02-14T12:00:00&then=2024-02-14T15:00:00
```

### GET /tomorrow
Get weather condition indicators for tomorrow.

Parameters:
- `now`: ISO datetime string (e.g., "2024-02-14T12:00:00")

Example:
```
GET /tomorrow?now=2024-02-14T12:00:00
```

## Running Tests
```bash
pytest tests/
```

## TODOs
- Add input validation for datetime formats
- Implement caching for frequent requests
- Add more comprehensive error handling
- Add more test cases for edge scenarios