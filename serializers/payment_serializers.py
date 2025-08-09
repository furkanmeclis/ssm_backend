from rest_framework import serializers
from paytr.models import PaymentPlan

class PaymentPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentPlan
        fields = ['id', 'title', 'description', 'days', 'final_price', 'discount', 'is_active']
