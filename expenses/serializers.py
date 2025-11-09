from rest_framework import serializers
from .models import Expense

class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = [
            'id', 'name', 'category', 'value', 'type_expense', 'date'
        ]

        read_only_fields = ['id']

        def validate_value(self, value):
            if value < 0:
                raise serializers.ValidationError("O valor da despesa não pode ser menor ou igual a zero.")
            return True