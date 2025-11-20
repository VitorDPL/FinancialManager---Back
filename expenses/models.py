from django.db import models
from categories.models import Category
from datetime import date

# Create your models here.
class Expense(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, default="Não informado/ Gerais")
    category = models.ForeignKey('categories.Category', on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    type_expense = models.CharField(default = 'à vista', choices = [('à vista', 'à vista'), ('parcelado', 'parcelado'), ('mensal', 'mensal')]) #se parcelado, cria-se um registro na tabela de parcelas
    date = models.DateField(default = date.today)
    
    def __str__(self):
        return f"{self.name} - {self.category} - {self.value} - {self.type_expense} - {self.date}"

