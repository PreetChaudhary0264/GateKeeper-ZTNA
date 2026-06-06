# Ye hamari fake database hai
# Real project mein PostgreSQL se aayega

USERS = {
    "ims@company.com": {
        "password": "pass123",
        "role": "hr",
        "name": "ims",
        "device_id": "DEVICE-HR-001"    # registered device
    },
    "priya@company.com": {
        "password": "pass456",
        "role": "finance",
        "name": "Priya",
        "device_id": "DEVICE-FIN-002"   # registered device
    },
    "admin@company.com": {
        "password": "admin789",
        "role": "admin",
        "name": "Admin",
        "device_id": "DEVICE-ADM-003"   # registered device
    }
}

# Company ke registered devices
# Sirf ye devices access kar sakte hain
REGISTERED_DEVICES = [
    "DEVICE-HR-001",
    "DEVICE-FIN-002", 
    "DEVICE-ADM-003",
]

def get_user(email: str):
    return USERS.get(email)

def is_device_registered(device_id: str) -> bool:
    return device_id in REGISTERED_DEVICES