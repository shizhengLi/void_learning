# Demo Project

This is a simple demo project to test the code editor agent.

## Modules

- **calculator.py**: Simple calculator with basic operations
- **geometry.py**: Geometry functions for calculating areas and perimeters

## Usage

```python
# Using the calculator
from src.calculator import add, subtract, multiply, divide

result = add(5, 3)  # Returns 8

# Using the geometry module
from src.geometry import calculate_circle_area

area = calculate_circle_area(5)  # Returns the area of a circle with radius 5
```

## TODOs

- Add triangle calculations to the geometry module
- Add error handling to the divide function in calculator
- Create a unified math library combining both modules 