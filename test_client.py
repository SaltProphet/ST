#!/usr/bin/env python3
"""Simple CLI client to test WebSocket telemetry streaming"""

import asyncio
import json
import sys

try:
    import websockets
except ImportError:
    print("Error: websockets library not installed")
    print("Run: pip install websockets")
    sys.exit(1)


async def test_client(url: str = "ws://localhost:8000/ws", duration: int = 5):
    """Connect to WebSocket and display telemetry data"""
    
    print(f"Connecting to {url}...")
    
    try:
        async with websockets.connect(url) as websocket:
            print("✅ Connected!")
            print("Receiving telemetry data...\n")
            
            start_time = asyncio.get_event_loop().time()
            message_count = 0
            
            while (asyncio.get_event_loop().time() - start_time) < duration:
                try:
                    # Receive message
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    message_count += 1
                    
                    # Display data
                    print(f"[{message_count}] Telemetry Update:")
                    print(f"  Boost:     {data['boost']['psi']:>7.2f} PSI {' ⚠️' if data['boost']['warning'] else ''}")
                    print(f"  Oil Temp:  {data['oil_temp']['fahrenheit']:>7.1f} °F  {' ⚠️' if data['oil_temp']['warning'] else ''}")
                    print(f"  OAR:       {data['oar']['value']:>7.3f}     {' ⚠️' if data['oar']['warning'] else ''}")
                    print()
                    
                except asyncio.TimeoutError:
                    continue
                    
            print(f"\n✅ Test complete! Received {message_count} messages in {duration} seconds")
            print(f"   Average rate: {message_count/duration:.1f} Hz")
            
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Focus ST Telemetry WebSocket")
    parser.add_argument("--url", default="ws://localhost:8000/ws", help="WebSocket URL")
    parser.add_argument("--duration", type=int, default=5, help="Test duration in seconds")
    
    args = parser.parse_args()
    
    asyncio.run(test_client(args.url, args.duration))
