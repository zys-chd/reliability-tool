"""
Unit conversion to SI standard units for FT test data.
"""

import re
from typing import Optional, Union

# SI prefix multipliers
SI_PREFIXES = {
    'f': 1e-15, 'p': 1e-12, 'n': 1e-9, 'u': 1e-6, 'μ': 1e-6,
    'm': 1e-3, 'c': 1e-2, 'd': 1e-1,
    'da': 1e1, 'h': 1e2, 'k': 1e3, 'M': 1e6, 'G': 1e9, 'T': 1e12,
}

# Base SI units for common measurements
BASE_UNITS = {
    'V': 'V',       # Voltage
    'A': 'A',       # Current
    'Ω': 'Ω',       # Resistance (ohm)
    'OHM': 'Ω',
    'OHMS': 'Ω',
    'W': 'W',       # Power
    'F': 'F',       # Capacitance
    'H': 'H',       # Inductance
    'S': 'S',       # Conductance (siemens)
    'HZ': 'Hz',     # Frequency
    'Hz': 'Hz',
    'C': 'C',       # Coulombs
    '°C': '°C',     # Temperature Celsius
    'K': 'K',       # Kelvin
    '%': '%',       # Percentage
    's': 's',       # Time (seconds)
    'SEC': 's',
    'MIN': 'min',
    'MS': 's',      # milliseconds → seconds
    'US': 's',      # microseconds → seconds
    'NS': 's',      # nanoseconds → seconds
}

# Unit conversion functions for non-SI units
UNIT_CONVERTERS = {
    # {from_unit: (to_unit, conversion_factor_or_fn)}
    '°F': ('°C', lambda v: (v - 32) * 5/9),
    'inch': ('m', 0.0254),
    'mil': ('m', 2.54e-5),
}


class UnitConverter:
    """Convert measurement units to SI standard units."""
    
    @staticmethod
    def parse_unit(unit_str: str) -> tuple[str, float]:
        """Parse a unit string into (base_unit_si, multiplier).
        
        Returns: (si_unit_name, multiplier_to_convert_to_si)
        Example: 'mA' → ('A', 0.001), 'kV' → ('V', 1000)
        """
        unit = unit_str.strip()
        if not unit:
            return ('', 1.0)
        
        unit_upper = unit.upper()
        
        # Check for direct conversion
        if unit_upper in BASE_UNITS:
            return (BASE_UNITS[unit_upper], 1.0)
        
        # Check for custom converters
        if unit in UNIT_CONVERTERS:
            to_unit = UNIT_CONVERTERS[unit][0]
            multiplier = UNIT_CONVERTERS[unit][1]
            return (to_unit, multiplier)
        
        # Try to split prefix + base unit (2-char prefix first like 'da')
        for prefix_len in [2, 1]:
            if len(unit) > prefix_len:
                prefix = unit[:prefix_len]
                base = unit[prefix_len:]
                if prefix in SI_PREFIXES and base.upper() in BASE_UNITS:
                    multiplier = SI_PREFIXES[prefix]
                    base_si = BASE_UNITS[base.upper()]
                    return (base_si, multiplier)
        
        # Also check with first char as prefix
        if len(unit) > 1:
            prefix = unit[0]
            base = unit[1:]
            if prefix in SI_PREFIXES and base.upper() in BASE_UNITS:
                multiplier = SI_PREFIXES[prefix]
                base_si = BASE_UNITS[base.upper()]
                return (base_si, multiplier)
        
        return (unit, 1.0)  # Unknown unit, return as-is
    
    @staticmethod
    def convert(value: float, from_unit: str) -> tuple[float, str]:
        """Convert a value from a unit to SI standard.
        
        Returns: (converted_value, si_unit_name)
        """
        si_unit, multiplier = UnitConverter.parse_unit(from_unit)
        if callable(multiplier):
            converted = multiplier(value)
        else:
            converted = value * multiplier
        return (converted, si_unit)
    
    @staticmethod
    def normalize_unit_display(unit_str: str) -> str:
        """Normalize a unit string to SI display form.
        
        'uA' → 'µA', 'mA' → 'mA', 'V' → 'V'
        """
        si_unit, _ = UnitConverter.parse_unit(unit_str)
        return si_unit or unit_str
