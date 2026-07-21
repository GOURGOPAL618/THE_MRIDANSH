# THE MRIDANSH - WEATHER SCHEMA

from pydantic import BaseModel, Field

class WeatherTelemetry(BaseModel):
    """Validates real-time meteorology metrics for soil hydration dynamics"""
    precipitation_mm: float = Field(..., ge=0.0, le=1000.0, description="Precipitation in mm/day")
    surface_temperature_k: float = Field(..., ge=200.0, le=350.0, description="Temperature in Kelvin")
    relative_humidity: float = Field(..., ge=0.0, le=100.0, description="Relative humidity %")
    surface_pressure_hpa: float = Field(default=1013.25, ge=800.0, le=1100.0)

# Self-test block
if __name__ == "__main__":
    sample_weather = WeatherTelemetry(
        precipitation_mm = 14.5,
        surface_temperature_k = 301.15,
        relative_humidity = 65.0
    )

    print("✅ Weather Schema Validation Passed!")
    print(f"Precipitation: {sample_weather.precipitation_mm}mm | Temp: {sample_weather.surface_temperature_k}K")