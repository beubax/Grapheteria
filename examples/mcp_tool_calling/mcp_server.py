# mcp_server.py
from fastmcp import FastMCP

# Create a named server
mcp = FastMCP("Research Assistant Server")

@mcp.tool()
def calculate(expression: str) -> float:
    """Evaluate a mathematical expression safely"""
    # In a real application, use a safer evaluation method
    return eval(expression, {"__builtins__": {}}, {"abs": abs, "round": round, "max": max, "min": min})

@mcp.tool()
def get_country_info(country: str) -> dict:
    """Get basic information about a country"""
    countries = {
        "france": {"capital": "Paris", "population": "67 million", "language": "French"},
        "japan": {"capital": "Tokyo", "population": "126 million", "language": "Japanese"},
        "brazil": {"capital": "Brasília", "population": "213 million", "language": "Portuguese"},
    }
    return countries.get(country.lower(), {"error": "Country not found"})

@mcp.tool()
def convert_units(value: float, from_unit: str, to_unit: str) -> float:
    """Convert between common units"""
    conversions = {
        "km_to_miles": 0.621371,
        "miles_to_km": 1.60934,
        "kg_to_lb": 2.20462,
        "lb_to_kg": 0.453592,
        "celsius_to_fahrenheit": lambda x: x * 9/5 + 32,
        "fahrenheit_to_celsius": lambda x: (x - 32) * 5/9,
    }
    
    key = f"{from_unit.lower()}_to_{to_unit.lower()}"
    if key in conversions:
        converter = conversions[key]
        if callable(converter):
            return converter(value)
        return value * converter
    return {"error": "Conversion not supported"}

# Start the server
if __name__ == "__main__":
    mcp.run()
