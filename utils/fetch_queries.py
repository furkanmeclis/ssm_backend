from django.utils import timezone
from datetime import timedelta, datetime
from django.utils.dateparse import parse_datetime
import os

def get_date_range_from_request(request):
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    days = request.query_params.get('days')

    if days:
        days = int(days)  # Convert days to an integer
        end_date = timezone.localtime()
        start_date = end_date - timedelta(days=days)
    else:
        # Ensure start_date and end_date are converted to timezone-aware datetimes
        start_date = parse_datetime(start_date + "T00:00:00Z") if start_date else timezone.make_aware(datetime.min)
        end_date = parse_datetime(end_date + "T23:59:59Z") if end_date else timezone.localtime()

    return start_date, end_date

def get_merchant_credentials():
    return (
        os.environ.get('MERCHANT_ID'),
        os.environ.get('MERCHANT_KEY'),
        os.environ.get('MERCHANT_SALT')
    )
