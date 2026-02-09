"""Alert system for monitoring telemetry thresholds."""
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Callable
from datetime import datetime
from config import settings
from database import db


class AlertEvaluator:
    """Evaluates telemetry data against configured alert conditions."""
    
    CONDITION_OPS = {
        "gt": lambda v, t: v > t,      # greater than
        "gte": lambda v, t: v >= t,    # greater than or equal
        "lt": lambda v, t: v < t,      # less than
        "lte": lambda v, t: v <= t,    # less than or equal
        "eq": lambda v, t: v == t,     # equal
        "neq": lambda v, t: v != t,    # not equal
    }
    
    def __init__(self):
        self.alert_configs = []
        self.callbacks = []
    
    async def load_alerts(self):
        """Load alert configurations from database."""
        self.alert_configs = await db.get_alerts(enabled_only=True)
    
    def register_callback(self, callback: Callable):
        """Register a callback function for alert triggers."""
        self.callbacks.append(callback)
    
    async def evaluate(self, session_id: str, pid: str, value: float):
        """Evaluate a telemetry reading against all relevant alerts."""
        triggered_alerts = []
        
        for alert in self.alert_configs:
            if alert["pid"] != pid:
                continue
            
            condition_op = self.CONDITION_OPS.get(alert["condition"])
            if not condition_op:
                continue
            
            if condition_op(value, alert["threshold"]):
                message = f"Alert '{alert['name']}': {pid} = {value} {alert['condition']} {alert['threshold']}"
                
                # Log to database
                await db.log_alert(
                    alert["id"],
                    session_id,
                    pid,
                    value,
                    message
                )
                
                alert_data = {
                    "alert_id": alert["id"],
                    "name": alert["name"],
                    "pid": pid,
                    "value": value,
                    "threshold": alert["threshold"],
                    "condition": alert["condition"],
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
                
                triggered_alerts.append(alert_data)
                
                # Send notifications
                if alert["email_notify"] and settings.enable_email_alerts:
                    await self._send_email_notification(alert_data)
                
                # Call registered callbacks
                for callback in self.callbacks:
                    try:
                        await callback(alert_data)
                    except Exception as e:
                        print(f"Error in alert callback: {e}")
        
        return triggered_alerts
    
    async def _send_email_notification(self, alert_data: Dict):
        """Send email notification for alert."""
        if not settings.smtp_user or not settings.smtp_password or not settings.alert_email_to:
            return
        
        try:
            msg = MIMEMultipart()
            msg["From"] = settings.smtp_user
            msg["To"] = settings.alert_email_to
            msg["Subject"] = f"ST Telemetry Alert: {alert_data['name']}"
            
            body = f"""
            Alert Triggered
            
            Name: {alert_data['name']}
            PID: {alert_data['pid']}
            Current Value: {alert_data['value']}
            Threshold: {alert_data['threshold']}
            Condition: {alert_data['condition']}
            Time: {alert_data['timestamp']}
            
            Message: {alert_data['message']}
            """
            
            msg.attach(MIMEText(body, "plain"))
            
            # Send email in a thread pool to avoid blocking
            await asyncio.to_thread(self._send_smtp, msg)
            
        except Exception as e:
            print(f"Failed to send email alert: {e}")
    
    def _send_smtp(self, msg: MIMEMultipart):
        """Send SMTP email (blocking operation)."""
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
        server.quit()


class CloudSync:
    """Synchronize telemetry data to cloud services."""
    
    def __init__(self):
        self.enabled = settings.enable_cloud_sync
        self.api_url = settings.cloud_api_url
        self.api_key = settings.cloud_api_key
        self.queue = asyncio.Queue(maxsize=1000)
    
    async def push(self, data: Dict):
        """Push telemetry data to cloud."""
        if not self.enabled:
            return
        
        try:
            await self.queue.put(data)
        except asyncio.QueueFull:
            print("Cloud sync queue full, dropping data")
    
    async def worker(self):
        """Background worker to process cloud sync queue."""
        if not self.enabled or not self.api_url:
            return
        
        while True:
            try:
                data = await self.queue.get()
                # Placeholder for actual cloud API call
                # import httpx
                # async with httpx.AsyncClient() as client:
                #     await client.post(
                #         self.api_url,
                #         json=data,
                #         headers={"Authorization": f"Bearer {self.api_key}"}
                #     )
                print(f"Cloud sync: {data['pid']} = {data['value']}")
                self.queue.task_done()
            except Exception as e:
                print(f"Cloud sync error: {e}")
                await asyncio.sleep(5)


# Global instances
alert_evaluator = AlertEvaluator()
cloud_sync = CloudSync()
