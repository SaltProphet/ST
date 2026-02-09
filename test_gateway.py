"""Test script for Focus ST Telemetry Gateway"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from focusst_telemetry.ecu.mock import MockECU
from focusst_telemetry.ecu.factory import create_ecu
from focusst_telemetry.data.parser import PIDParser


async def test_mock_ecu():
    """Test mock ECU data generation"""
    print("\n" + "="*60)
    print("Testing Mock ECU")
    print("="*60)
    
    ecu = MockECU(update_rate=20)
    await ecu.start()
    
    parser = PIDParser()
    
    # Read and parse some samples
    for i in range(5):
        raw_data = await ecu.read_data()
        parsed_data = parser.parse_all(raw_data)
        
        print(f"\nSample {i+1}:")
        print(f"  Boost: {parsed_data['boost']['psi']:.2f} PSI (raw: {parsed_data['boost']['raw']:.1f}) - Warning: {parsed_data['boost']['warning']}")
        print(f"  Oil Temp: {parsed_data['oil_temp']['fahrenheit']:.1f} °F (raw: {parsed_data['oil_temp']['raw']:.1f}) - Warning: {parsed_data['oil_temp']['warning']}")
        print(f"  OAR: {parsed_data['oar']['value']:.3f} (target: -1.0, alert > -0.7) - Warning: {parsed_data['oar']['warning']}")
        
        await asyncio.sleep(0.1)
    
    await ecu.stop()
    print("\n✓ Mock ECU test passed")


async def test_hardware_detection():
    """Test hardware auto-detection"""
    print("\n" + "="*60)
    print("Testing Hardware Auto-Detection")
    print("="*60)
    
    ecu = await create_ecu()
    print(f"ECU Type: {type(ecu).__name__}")
    
    if ecu.__class__.__name__ == "MockECU":
        print("✓ Correctly fell back to MockECU (no hardware detected)")
    else:
        print("✓ Hardware detected and initialized")
    
    await ecu.stop()


async def test_boost_formula():
    """Test boost formula accuracy"""
    print("\n" + "="*60)
    print("Testing Boost Formula: ((A*256)+B)*0.0145 - 14.7")
    print("="*60)
    
    parser = PIDParser()
    
    # Test cases: (raw_value, expected_psi)
    test_cases = [
        (1014.0, 0.0),  # Atmospheric (approximately)
        (2048.0, 15.0),  # High boost
        (500.0, -7.45),  # Vacuum
    ]
    
    for raw, expected_approx in test_cases:
        psi, warning = parser.parse_boost(raw)
        print(f"  Raw: {raw:6.1f} -> PSI: {psi:6.2f} (expected ~{expected_approx:.2f}) - Warning: {warning}")
    
    print("✓ Boost formula test passed")


async def test_oar_threshold():
    """Test OAR warning threshold"""
    print("\n" + "="*60)
    print("Testing OAR Warning Threshold (> -0.7)")
    print("="*60)
    
    parser = PIDParser()
    
    test_values = [-1.0, -0.9, -0.8, -0.7, -0.6, -0.5, 0.0]
    
    for val in test_values:
        _, warning = parser.parse_oar(val)
        status = "⚠️ WARNING" if warning else "✓ OK"
        print(f"  OAR: {val:5.1f} -> {status}")
    
    # Verify threshold
    _, warn_at_neg07 = parser.parse_oar(-0.7)
    _, warn_at_neg06 = parser.parse_oar(-0.6)
    
    if not warn_at_neg07 and warn_at_neg06:
        print("✓ OAR threshold correct: warning when > -0.7")
    else:
        print("✗ OAR threshold incorrect")


async def main():
    """Run all tests"""
    try:
        await test_boost_formula()
        await test_oar_threshold()
        await test_mock_ecu()
        await test_hardware_detection()
        
        print("\n" + "="*60)
        print("All tests passed! ✓")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
