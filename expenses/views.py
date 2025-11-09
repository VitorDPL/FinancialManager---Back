from django.http import JsonResponse
from rest_framework.views import APIView
from .serializers import ExpenseSerializer
from rest_framework.response import Response
from rest_framework import status
from installments.models import Installment
from django.views.generic.detail import DetailView
from . models import Expense

# Create your views here.
class ExpenseView(APIView):
    def post(self, request):
        serializer = ExpenseSerializer(data=request.data)
        try:
            if serializer.is_valid():
                expense = serializer.save()
                
                if expense.type_expense == 'parcelado':
                    number_of_installments = request.data.get('number_of_installments')

                    Installment.objects.create(
                        number_of_installments=number_of_installments,
                        expense_id=expense,
                    )

                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return JsonResponse({
                "error: " : f"Ocorreu um erro ao inserir o novo gasto: {e}"
            })
        
    def get(self, request, *args, **kwargs):
        try:
            print("----CHEGAMOS AQUI-----")

            expenses = Expense.objects.all()
            serializer = ExpenseSerializer(expenses, many=True)

            print("Exibindo o serializer: ", serializer)

            return Response(
                    serializer.data
            )

        except Exception as e:
            return JsonResponse("error: ", e)