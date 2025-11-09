from django.db import models
from expenses.models import Expense

# Create your models here.
class Installment(models.Model):
    id = models.AutoField(primary_key=True)
    number_of_installments = models.IntegerField(default= 2)
    expense_id = models.ForeignKey('expenses.Expense', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.expense_id.name} - {self.number_of_installments}x"