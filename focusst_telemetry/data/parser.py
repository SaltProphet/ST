"""PID-specific parsing and conversion logic"""

from typing import Dict, Any, Tuple


class PIDParser:
    """Handles parsing and conversion of PID data"""
    
    @staticmethod
    def parse_boost(raw_value: float) -> Tuple[float, bool]:
        """Parse boost pressure from raw value
        
        Formula: PSI = raw_value * 0.0145 - 14.7
        
        Args:
            raw_value: Raw boost value from ECU
            
        Returns:
            Tuple of (psi_value, is_warning)
            is_warning is True if boost is dangerously high (>20 PSI)
        """
        psi = raw_value * 0.0145 - 14.7
        is_warning = psi > 20.0  # Warning threshold for high boost
        return psi, is_warning
    
    @staticmethod
    def parse_oil_temp(raw_value: float) -> Tuple[float, bool]:
        """Parse oil temperature
        
        Args:
            raw_value: Raw temperature value (assumed to be in Fahrenheit)
            
        Returns:
            Tuple of (temp_f, is_warning)
            is_warning is True if temp is outside safe range (160-240°F)
        """
        temp_f = raw_value
        is_warning = temp_f < 160.0 or temp_f > 240.0
        return temp_f, is_warning
    
    @staticmethod
    def parse_oar(raw_value: float) -> Tuple[float, bool]:
        """Parse Oxygen/Air Ratio
        
        OAR should be near -1.0 for proper operation.
        
        Args:
            raw_value: Raw OAR value
            
        Returns:
            Tuple of (oar_value, is_warning)
            is_warning is True if OAR deviates significantly from -1.0
        """
        oar = raw_value
        # Flag warning if not near -1.0 (tolerance: ±0.3)
        is_warning = abs(oar - (-1.0)) > 0.3
        return oar, is_warning
    
    @classmethod
    def parse_all(cls, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse all PID data and add derived values
        
        Args:
            raw_data: Dict with raw PID values
            
        Returns:
            Dict with parsed values and warning flags
        """
        boost_psi, boost_warning = cls.parse_boost(raw_data["boost"])
        oil_temp_f, oil_temp_warning = cls.parse_oil_temp(raw_data["oil_temp"])
        oar_value, oar_warning = cls.parse_oar(raw_data["oar"])
        
        return {
            "timestamp": raw_data["timestamp"],
            "boost": {
                "raw": raw_data["boost"],
                "psi": round(boost_psi, 2),
                "warning": boost_warning,
            },
            "oil_temp": {
                "raw": raw_data["oil_temp"],
                "fahrenheit": round(oil_temp_f, 1),
                "warning": oil_temp_warning,
            },
            "oar": {
                "value": round(oar_value, 3),
                "warning": oar_warning,
            },
        }
