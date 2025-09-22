# backend/sla/sla_utils.py
from datetime import timedelta

# SLA rules in hours (change to seconds for fast testing)
SLA_RULES = {
    "low": 12,     
    "medium": 6,  
    "high": 3,     
    "urgent": 1   
}

def calculate_sla_deadline(priority: str):
    hours = SLA_RULES.get(priority.lower(), 6)
    from datetime import datetime, timedelta
    return datetime.utcnow() + timedelta(hours=hours)
