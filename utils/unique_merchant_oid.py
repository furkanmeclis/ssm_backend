import uuid
from paytr.models import Payment

def generate_unique_merchant_oid():
    while True:
        merchant_oid = str(uuid.uuid4()).replace('-', '')[:20]
        if not Payment.objects.filter(merchant_oid=merchant_oid).exists():
            return merchant_oid
