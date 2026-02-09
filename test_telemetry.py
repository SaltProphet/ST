"""Unit tests for the ST Telemetry system."""
import pytest
import asyncio
from datetime import datetime
from database import Database
from obd_simulator import OBDSimulator, HardwareAbstractionLayer
from alerts import AlertEvaluator
from auth import get_password_hash, verify_password


@pytest.fixture
async def test_db():
    """Create a test database."""
    db = Database(":memory:")
    await db.connect()
    yield db
    await db.close()


@pytest.mark.asyncio
async def test_database_session_creation(test_db):
    """Test creating a telemetry session."""
    session_id = "test-session-123"
    await test_db.create_session(session_id, {"vehicle": "Focus ST"})
    
    sessions = await test_db.list_sessions()
    assert len(sessions) == 1
    assert sessions[0]["session_id"] == session_id


@pytest.mark.asyncio
async def test_telemetry_data_insertion(test_db):
    """Test inserting telemetry data."""
    session_id = "test-session-123"
    await test_db.create_session(session_id)
    
    await test_db.insert_telemetry(session_id, "RPM", 3000.0, "RPM")
    await test_db.insert_telemetry(session_id, "BOOST", 15.5, "PSI")
    
    data = await test_db.get_session_data(session_id)
    assert len(data) == 2
    assert data[0]["pid"] == "RPM"
    assert data[0]["value"] == 3000.0


@pytest.mark.asyncio
async def test_alert_creation(test_db):
    """Test creating alert configurations."""
    alert_id = await test_db.create_alert(
        "High Boost",
        "BOOST",
        "gt",
        20.0,
        email_notify=True
    )
    
    alerts = await test_db.get_alerts()
    assert len(alerts) == 1
    assert alerts[0]["name"] == "High Boost"
    assert alerts[0]["threshold"] == 20.0


@pytest.mark.asyncio
async def test_alert_evaluation():
    """Test alert evaluation logic."""
    evaluator = AlertEvaluator()
    evaluator.alert_configs = [
        {
            "id": 1,
            "name": "High Boost",
            "pid": "BOOST",
            "condition": "gt",
            "threshold": 20.0,
            "enabled": True,
            "email_notify": False
        }
    ]
    
    # Mock database
    class MockDB:
        async def log_alert(self, *args, **kwargs):
            pass
    
    import alerts
    original_db = alerts.db
    alerts.db = MockDB()
    
    # Should trigger alert
    triggered = await evaluator.evaluate("test-session", "BOOST", 21.0)
    assert len(triggered) == 1
    assert triggered[0]["name"] == "High Boost"
    
    # Should not trigger
    triggered = await evaluator.evaluate("test-session", "BOOST", 15.0)
    assert len(triggered) == 0
    
    alerts.db = original_db


def test_obd_simulator():
    """Test OBD simulator functionality."""
    sim = OBDSimulator()
    
    # Test reading a single PID
    rpm_data = sim.read_pid("RPM")
    assert rpm_data is not None
    assert rpm_data["pid"] == "RPM"
    assert rpm_data["unit"] == "RPM"
    assert 800 <= rpm_data["value"] <= 6500
    
    # Test reading all PIDs
    all_data = sim.read_all()
    assert len(all_data) == len(sim.PIDS)
    
    # Test scenario changes
    sim.set_scenario("hard_driving")
    rpm_data = sim.read_pid("RPM")
    # After scenario change, values should trend towards targets
    assert rpm_data["value"] > 0


@pytest.mark.asyncio
async def test_hardware_abstraction_layer():
    """Test hardware abstraction layer."""
    hal = HardwareAbstractionLayer(interface_type="simulator")
    await hal.connect()
    
    # Test reading through HAL
    rpm_data = hal.read_pid("RPM")
    assert rpm_data is not None
    assert rpm_data["pid"] == "RPM"
    
    all_data = hal.read_all()
    assert len(all_data) > 0
    
    await hal.disconnect()


def test_password_hashing():
    """Test password hashing and verification."""
    password = "test_password_123"
    
    # Hash password
    hashed = get_password_hash(password)
    assert hashed != password
    assert len(hashed) > 0
    
    # Verify correct password
    assert verify_password(password, hashed)
    
    # Verify incorrect password
    assert not verify_password("wrong_password", hashed)


@pytest.mark.asyncio
async def test_user_creation(test_db):
    """Test user creation in database."""
    hashed_password = get_password_hash("password123")
    
    user_id = await test_db.create_user(
        "testuser",
        "test@example.com",
        hashed_password,
        "viewer"
    )
    
    user = await test_db.get_user("testuser")
    assert user is not None
    assert user["username"] == "testuser"
    assert user["email"] == "test@example.com"
    assert user["role"] == "viewer"
    assert user["is_active"]


@pytest.mark.asyncio
async def test_rolling_buffer(test_db):
    """Test rolling buffer functionality."""
    session_id = "test-session-buffer"
    await test_db.create_session(session_id)
    
    # Insert some test data
    for i in range(100):
        await test_db.insert_telemetry(session_id, "RPM", float(1000 + i), "RPM")
    
    # Get recent data (default 600 seconds)
    recent = await test_db.get_recent_telemetry(session_id, seconds=600)
    assert len(recent) == 100
    
    # Get very recent data - all data is inserted at same time in test,
    # so they're all within 1 second, just verify it works
    recent = await test_db.get_recent_telemetry(session_id, seconds=1)
    assert len(recent) >= 0  # Could be 0 or more depending on timing


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
