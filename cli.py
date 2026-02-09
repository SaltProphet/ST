#!/usr/bin/env python3
"""Command-line interface for ST Telemetry system diagnostics and management."""
import asyncio
import argparse
import sys
from datetime import datetime, timedelta
from typing import Optional
import json

from database import Database
from obd_simulator import OBDSimulator
from config import settings


class STCli:
    """CLI for managing the ST Telemetry system."""
    
    def __init__(self):
        self.db = Database()
    
    async def setup(self):
        """Initialize database connection."""
        await self.db.connect()
    
    async def cleanup(self):
        """Cleanup resources."""
        await self.db.close()
    
    async def list_sessions(self, limit: int = 10):
        """List recent telemetry sessions."""
        sessions = await self.db.list_sessions(limit)
        
        print(f"\n{'Session ID':<38} {'Start Time':<25} {'End Time':<25}")
        print("-" * 90)
        
        for session in sessions:
            end_time = session['end_time'] or 'Active'
            print(f"{session['session_id']:<38} {session['start_time']:<25} {end_time:<25}")
        
        print(f"\nTotal: {len(sessions)} sessions\n")
    
    async def show_session(self, session_id: str, limit: int = 100):
        """Show telemetry data for a specific session."""
        data = await self.db.get_session_data(session_id)
        
        if not data:
            print(f"No data found for session {session_id}")
            return
        
        print(f"\nSession: {session_id}")
        print(f"Data points: {len(data)}")
        print(f"\n{'Timestamp':<25} {'PID':<20} {'Value':<15} {'Unit':<10}")
        print("-" * 70)
        
        for point in data[:limit]:
            print(f"{point['timestamp']:<25} {point['pid']:<20} {point['value']:<15.2f} {point['unit']:<10}")
        
        if len(data) > limit:
            print(f"\n... and {len(data) - limit} more data points")
        print()
    
    async def export_session(self, session_id: str, output_file: str, format: str = 'csv'):
        """Export session data to file."""
        data = await self.db.get_session_data(session_id)
        
        if not data:
            print(f"No data found for session {session_id}")
            return
        
        if format == 'csv':
            import csv
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['timestamp', 'pid', 'value', 'unit'])
                writer.writeheader()
                writer.writerows(data)
        elif format == 'json':
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
        
        print(f"Exported {len(data)} data points to {output_file}")
    
    async def list_alerts(self):
        """List all alert configurations."""
        alerts = await self.db.get_alerts(enabled_only=False)
        
        print(f"\n{'ID':<5} {'Name':<25} {'PID':<15} {'Condition':<10} {'Threshold':<12} {'Enabled':<8} {'Email':<8}")
        print("-" * 90)
        
        for alert in alerts:
            enabled = '✓' if alert['enabled'] else '✗'
            email = '✓' if alert['email_notify'] else '✗'
            print(f"{alert['id']:<5} {alert['name']:<25} {alert['pid']:<15} {alert['condition']:<10} {alert['threshold']:<12.2f} {enabled:<8} {email:<8}")
        
        print(f"\nTotal: {len(alerts)} alerts\n")
    
    async def create_alert(self, name: str, pid: str, condition: str, threshold: float, email: bool = False):
        """Create a new alert configuration."""
        alert_id = await self.db.create_alert(name, pid, condition, threshold, email)
        print(f"Created alert with ID: {alert_id}")
    
    async def test_simulator(self, duration: int = 10):
        """Test the OBD simulator."""
        print(f"Testing OBD simulator for {duration} seconds...\n")
        
        simulator = OBDSimulator()
        
        # Test different scenarios
        scenarios = ['idle', 'cruising', 'acceleration', 'hard_driving']
        
        for scenario in scenarios:
            print(f"\nScenario: {scenario.upper()}")
            simulator.set_scenario(scenario)
            
            # Read a few PIDs
            for _ in range(3):
                data = simulator.read_all()
                # Show first 5 PIDs
                for point in data[:5]:
                    print(f"  {point['pid']:<15} {point['value']:>8.2f} {point['unit']}")
                await asyncio.sleep(1)
    
    async def list_pids(self):
        """List all available PIDs."""
        simulator = OBDSimulator()
        
        print("\nAvailable PIDs:\n")
        print(f"{'PID':<20} {'Min':<10} {'Max':<10} {'Unit':<10}")
        print("-" * 50)
        
        for pid, config in sorted(simulator.PIDS.items()):
            print(f"{pid:<20} {config['min']:<10.1f} {config['max']:<10.1f} {config['unit']:<10}")
        
        print(f"\nTotal: {len(simulator.PIDS)} PIDs\n")
    
    async def cleanup_old_data(self, days: int = 30):
        """Clean up telemetry data older than specified days."""
        print(f"Cleaning up data older than {days} days...")
        await self.db.cleanup_old_data(days)
        print("Cleanup complete.")
    
    async def create_user(self, username: str, email: str, password: str, role: str = 'viewer'):
        """Create a new user."""
        from auth import get_password_hash
        
        hashed_password = get_password_hash(password)
        user_id = await self.db.create_user(username, email, hashed_password, role)
        print(f"Created user '{username}' with ID: {user_id}")


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Focus ST Telemetry CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Sessions commands
    sessions_parser = subparsers.add_parser('sessions', help='List telemetry sessions')
    sessions_parser.add_argument('--limit', type=int, default=10, help='Number of sessions to show')
    
    show_parser = subparsers.add_parser('show', help='Show session data')
    show_parser.add_argument('session_id', help='Session ID')
    show_parser.add_argument('--limit', type=int, default=100, help='Number of data points to show')
    
    export_parser = subparsers.add_parser('export', help='Export session data')
    export_parser.add_argument('session_id', help='Session ID')
    export_parser.add_argument('output', help='Output file path')
    export_parser.add_argument('--format', choices=['csv', 'json'], default='csv', help='Output format')
    
    # Alerts commands
    alerts_parser = subparsers.add_parser('alerts', help='List alert configurations')
    
    create_alert_parser = subparsers.add_parser('create-alert', help='Create a new alert')
    create_alert_parser.add_argument('name', help='Alert name')
    create_alert_parser.add_argument('pid', help='PID to monitor')
    create_alert_parser.add_argument('condition', choices=['gt', 'gte', 'lt', 'lte', 'eq', 'neq'], help='Condition')
    create_alert_parser.add_argument('threshold', type=float, help='Threshold value')
    create_alert_parser.add_argument('--email', action='store_true', help='Enable email notifications')
    
    # Simulator commands
    test_parser = subparsers.add_parser('test', help='Test OBD simulator')
    test_parser.add_argument('--duration', type=int, default=10, help='Test duration in seconds')
    
    pids_parser = subparsers.add_parser('pids', help='List available PIDs')
    
    # Maintenance commands
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old telemetry data')
    cleanup_parser.add_argument('--days', type=int, default=30, help='Delete data older than N days')
    
    # User commands
    user_parser = subparsers.add_parser('create-user', help='Create a new user')
    user_parser.add_argument('username', help='Username')
    user_parser.add_argument('email', help='Email address')
    user_parser.add_argument('password', help='Password')
    user_parser.add_argument('--role', choices=['viewer', 'operator', 'admin'], default='viewer', help='User role')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = STCli()
    await cli.setup()
    
    try:
        if args.command == 'sessions':
            await cli.list_sessions(args.limit)
        elif args.command == 'show':
            await cli.show_session(args.session_id, args.limit)
        elif args.command == 'export':
            await cli.export_session(args.session_id, args.output, args.format)
        elif args.command == 'alerts':
            await cli.list_alerts()
        elif args.command == 'create-alert':
            await cli.create_alert(args.name, args.pid, args.condition, args.threshold, args.email)
        elif args.command == 'test':
            await cli.test_simulator(args.duration)
        elif args.command == 'pids':
            await cli.list_pids()
        elif args.command == 'cleanup':
            await cli.cleanup_old_data(args.days)
        elif args.command == 'create-user':
            await cli.create_user(args.username, args.email, args.password, args.role)
    finally:
        await cli.cleanup()


if __name__ == '__main__':
    asyncio.run(main())
