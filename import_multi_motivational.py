import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'osym_backend.settings')
django.setup()
from quizzes.models import MultiSubjectMotivationalMessage

range_mapping = {
    '0-20%': 1,
    '20-40%': 2,
    '40-60%': 3,
    '60-80%': 4,
    '80-100%': 5
}

# Load data from the file
with open('motivational_messages.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Import general messages as multi-subject messages
for range_key, messages in data.items():
    range_id = range_mapping.get(range_key)
    if not range_id:
        print(f"Warning: Invalid range key '{range_key}'. Skipping.")
        continue
        
    for message in messages:
        # Create as multi-subject message
        MultiSubjectMotivationalMessage.objects.create(
            success_rate_range=range_id,
            message=message,
            is_active=True
        )

print("Multi-subject motivational messages imported successfully!")
