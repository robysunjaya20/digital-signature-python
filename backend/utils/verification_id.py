import uuid

def generate_verification_id():
    return uuid.uuid4().hex[:10]
