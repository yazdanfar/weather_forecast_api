import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


class WeatherDataHandler:
    def __init__(self, csv_path: str):
        """Initialize the data handler with the weather CSV file."""
        try:
            self.df = pd.read_csv(csv_path)
            # Convert datetime columns to pandas datetime and ensure UTC timezone
            self.df['event_start'] = pd.to_datetime(self.df['event_start'])

            # Convert belief_horizon from seconds to hours
            self.df['belief_horizon'] = self.df['belief_horizon_in_sec'] / 3600
            self.df['belief_time'] = self.df['event_start'] - pd.to_timedelta(self.df['belief_horizon'], unit='h')

            # Calculate thresholds based on actual data
            temp_data = self.df[self.df['sensor'] == 'temperature']['event_value']
            wind_data = self.df[self.df['sensor'] == 'wind_speed']['event_value']
            irr_data = self.df[self.df['sensor'] == 'irradiance']['event_value']

            # Set thresholds
            self.TEMP_THRESHOLD = np.percentile(temp_data, 75) if not temp_data.empty else 15.0
            self.WIND_THRESHOLD = np.percentile(wind_data, 75) if not wind_data.empty else 3.0
            self.IRR_THRESHOLD = np.percentile(irr_data, 75) if not irr_data.empty else 200.0

            logger.info(
                f"Data loaded successfully. Date range: {self.df['event_start'].min()} to {self.df['event_start'].max()}")
            logger.info(
                f"Thresholds - Temp: {self.TEMP_THRESHOLD:.1f}°C, Wind: {self.WIND_THRESHOLD:.1f}m/s, Irr: {self.IRR_THRESHOLD:.1f}W/m²")

        except Exception as e:
            raise RuntimeError(f"Failed to initialize weather data: {str(e)}")

    def get_forecasts(self, now: datetime, then: datetime) -> Dict[str, Optional[float]]:
        """Get the most recent forecasts for a specific time."""
        try:
            now_ts = pd.Timestamp(now)
            then_ts = pd.Timestamp(then)

            mask = (
                    (self.df['belief_time'] <= now_ts) &
                    (self.df['event_start'] == then_ts)
            )
            relevant_forecasts = self.df[mask]

            if relevant_forecasts.empty:
                raise ValueError(f"No forecasts available for {then} based on data available at {now}")

            latest_forecasts = (
                relevant_forecasts
                .sort_values('belief_time', ascending=False)
                .groupby('sensor')
                .first()
            )

            return {
                'temperature': latest_forecasts.loc[
                    'temperature', 'event_value'] if 'temperature' in latest_forecasts.index else None,
                'wind_speed': latest_forecasts.loc[
                    'wind_speed', 'event_value'] if 'wind_speed' in latest_forecasts.index else None,
                'irradiance': latest_forecasts.loc[
                    'irradiance', 'event_value'] if 'irradiance' in latest_forecasts.index else None
            }
        except Exception as e:
            logger.error(f"Error in get_forecasts: {str(e)}")
            raise

    def get_tomorrow_conditions(self, now: datetime) -> Dict[str, bool]:
        """Determine tomorrow's weather conditions."""
        try:
            now_ts = pd.Timestamp(now)

            # Define tomorrow's date range
            tomorrow_start = (now_ts + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow_end = tomorrow_start + timedelta(days=1)

            # Filter relevant forecasts
            mask = (
                    (self.df['belief_time'] <= now_ts) &
                    (self.df['event_start'] >= tomorrow_start) &
                    (self.df['event_start'] < tomorrow_end)
            )
            tomorrow_forecasts = self.df[mask]

            if tomorrow_forecasts.empty:
                raise ValueError(f"No forecasts available for tomorrow based on data available at {now}")

            latest_forecasts = (
                tomorrow_forecasts
                .sort_values('belief_time', ascending=False)
                .groupby(['event_start', 'sensor'])
                .first()
            )

            temps = latest_forecasts.xs('temperature', level='sensor')[
                'event_value'] if 'temperature' in latest_forecasts.index.get_level_values('sensor') else pd.Series()
            winds = latest_forecasts.xs('wind_speed', level='sensor')[
                'event_value'] if 'wind_speed' in latest_forecasts.index.get_level_values('sensor') else pd.Series()
            irrs = latest_forecasts.xs('irradiance', level='sensor')[
                'event_value'] if 'irradiance' in latest_forecasts.index.get_level_values('sensor') else pd.Series()

            return {
                'warm': any(temps > self.TEMP_THRESHOLD),
                'sunny': any(irrs > self.IRR_THRESHOLD),
                'windy': any(winds > self.WIND_THRESHOLD)
            }

        except Exception as e:
            logger.error(f"Error in get_tomorrow_conditions: {str(e)}")
            raise