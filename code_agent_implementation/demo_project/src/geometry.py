"""
A simple geometry module for calculating areas and perimeters.
"""

import math

def calculate_circle_area(radius):
    """Calculate the area of a circle."""
    return math.pi * radius * radius

def calculate_circle_perimeter(radius):
    """Calculate the perimeter of a circle."""
    return 2 * math.pi * radius

def calculate_rectangle_area(length, width):
    """Calculate the area of a rectangle."""
    return length * width

def calculate_rectangle_perimeter(length, width):
    """Calculate the perimeter of a rectangle."""
    return 2 * (length + width)

# TODO: Add functions for triangle calculations 