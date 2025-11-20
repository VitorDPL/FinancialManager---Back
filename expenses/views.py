from django.http import JsonResponse
from rest_framework.views import APIView
from .serializers import ExpenseSerializer
from rest_framework.response import Response
from rest_framework import status
from installments.models import Installment
from django.views.generic.detail import DetailView
from . models import Expense
import calendar
from django.db.models import Sum
from django.db import transaction
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Create your views here.
class ExpenseView(APIView):

    def post(self, request):
        print("POST recebido:", request.data)
        serializer = ExpenseSerializer(data=request.data)
        try:
            if serializer.is_valid():
                with transaction.atomic():
                    expense = serializer.save()
                    print(f"Expense criado: {expense}, tipo: {expense.type_expense}")

                    if expense.type_expense == 'parcelado':
                        print("Entrou no bloco de parcelado")
                        # 1 - pegar e validar número de parcelas
                        try:
                            number_of_installments = int(request.data.get('number_of_installments'))
                            print(f"Número de parcelas: {number_of_installments}")
                        except (TypeError, ValueError):
                            return Response(
                                {"error": "Número de parcelas inválido."},
                                status=status.HTTP_400_BAD_REQUEST
                            )

                        # 2 - criar Installment vinculado ao gasto principal
                        installment = Installment.objects.create(
                            number_of_installments=number_of_installments,
                            expense_id=expense,
                        )
                        print(f"Installment criado: {installment}")

                        # 3 - atualizar o valor da primeira parcela (já criada)
                        total_value = float(request.data.get('value'))
                        installment_value = total_value / number_of_installments
                        expense.value = installment_value
                        expense.save()
                        print(f"Valor atualizado: {installment_value}")

                        # 4 - criar apenas as parcelas RESTANTES (2ª em diante)
                        print(f"Criando parcelas de 1 a {number_of_installments-1}")
                        for parcela in range(1, number_of_installments):
                            new_date = expense.date + relativedelta(months=parcela)
                            print(f"Criando parcela {parcela+1} para data: {new_date}")

                            new_expense = Expense.objects.create(
                                name=expense.name,
                                category=expense.category,
                                value=installment_value,
                                type_expense='parcelado',
                                date=new_date,
                            )
                            print(f"Parcela criada: {new_expense}")
                    # elif expense.type_expense == 'mensal':
                    #     print("Entrou no bloco mensal (recorrente)")
                        
                    #     # criar 24 parcelas futuras (2 anos)
                    #     months_to_create = 24
                        
                    #     # atualizar o gasto original para ser o primeiro
                    #     expense.type_expense = 'mensal'
                    #     expense.save()
                        
                    #     # criar parcelas futuras
                    #     for month in range(1, months_to_create + 1):
                    #         new_date = expense.date + relativedelta(months=month)
                            
                    #         Expense.objects.create(
                    #             name=expense.name,
                    #             category=expense.category,
                    #             value=expense.value,
                    #             type_expense='mensal',
                    #             date=new_date,
                    #         )
                    #         print(f"Parcela mensal {month} criada: {new_date}")


                return Response(serializer.data, status=status.HTTP_201_CREATED)

            else:
                print("Serializer inválido:", serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f"Erro durante criação: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                "error": f"Ocorreu um erro ao inserir o novo gasto: {e}"
            })

from django.db.models import Q, Sum
from collections import defaultdict

class ExpenseViewPerMonth(APIView):
    """
        Retorna todos os gastos agrupados por mês, incluindo mensais propagados
    """
    def get(self, request):
        try:
            # pegar os parâmetros
            start_date = request.query_params.get('start')
            end_date = request.query_params.get('end')

            # buscar TODOS os gastos mensais (sem filtro de data)
            monthly_expenses = Expense.objects.filter(type_expense='mensal')
            
            # buscar gastos não-mensais COM filtro de data
            non_monthly_qs = Expense.objects.exclude(type_expense='mensal')
            if start_date:
                non_monthly_qs = non_monthly_qs.filter(date__gte=start_date)
            if end_date:
                non_monthly_qs = non_monthly_qs.filter(date__lte=end_date)

            # agrupar gastos não-mensais
            grouped_non_monthly = (
                non_monthly_qs
                .values('date__year', 'date__month')
                .annotate(total=Sum('value'))
                .order_by('date__year', 'date__month')
            )

            # criar dicionário para acumular totais
            totals_dict = defaultdict(float)
            
            # adicionar gastos não-mensais
            for item in grouped_non_monthly:
                year = item['date__year']
                month = item['date__month']
                key = (year, month)
                totals_dict[key] += float(item['total'] or 0)

            # definir range de propagação
            if start_date and end_date:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            elif end_date:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
                start_dt = datetime.today().date()
            else:
                start_dt = datetime.today().date()
                end_dt = start_dt + relativedelta(months=24)

            # processar gastos mensais - propagar para meses futuros
            for expense in monthly_expenses:
                # só propagar se o gasto mensal começou antes do fim do range
                if expense.date > end_dt:
                    continue
                
                # começar do max entre data do gasto e start_date
                current_date = max(expense.date, start_dt)
                
                # propagar até end_date
                while current_date <= end_dt:
                    key = (current_date.year, current_date.month)
                    totals_dict[key] += float(expense.value or 0)
                    current_date += relativedelta(months=1)

            # converter dicionário para listas ordenadas
            month_names = {
                1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr',
                5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago',
                9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
            }

            labels = []
            totals = []
            
            for (year, month) in sorted(totals_dict.keys()):
                labels.append(f"{month_names.get(month)}/{year}")
                totals.append(totals_dict[(year, month)])

            print(f"Labels: {labels}")
            print(f"Totals: {totals}")

            return Response({"labels": labels, "data": totals})
            
        except Exception as e:
            print(f"Erro: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=500)
        
class ExpensesViewUniqueMonth(APIView):
    def get(self, request):
        try:
            params = request.query_params.get('month')
            print(f"Parâmetro recebido: {params}")
            
            # definir mês/ano alvo
            if not params:
                target_month = datetime.today().month
                target_year = datetime.today().year
                print(f"Nenhum parâmetro informado, usando mês atual: {target_month}/{target_year}")
            else:
                # extrair mês e ano do parâmetro
                month = params[0:3]
                year = params[4:8]
                
                month_map = {
                    "Jan": 1, "Fev": 2, "Mar": 3, "Abr": 4, 
                    "Mai": 5, "Jun": 6, "Jul": 7, "Ago": 8, 
                    "Set": 9, "Out": 10, "Nov": 11, "Dez": 12
                }

                if month not in month_map:
                    return Response({"error": f"Mês '{month}' inválido"}, status=400)
                
                target_month = month_map[month]
                target_year = int(year)
            
            print(f"Buscando gastos para mês {target_month} de {target_year}")

            # buscar TODOS os gastos mensais (independente do mês)
            monthly_expenses = Expense.objects.filter(type_expense='mensal')
            
            # buscar gastos não-mensais do mês específico
            non_monthly_expenses = Expense.objects.filter(
                date__month=target_month,
                date__year=target_year
            ).exclude(type_expense='mensal').order_by('date')

            # lista para acumular todos os gastos
            all_expenses = []

            # adicionar gastos não-mensais
            all_expenses.extend(non_monthly_expenses)

            # adicionar gastos mensais que devem aparecer neste mês
            for expense in monthly_expenses:
                # se o gasto mensal começou antes ou no mês alvo, incluir
                if expense.date.year < target_year or \
                   (expense.date.year == target_year and expense.date.month <= target_month):
                    all_expenses.append(expense)

            print(f"Encontrados {len(all_expenses)} gastos (incluindo mensais propagados)")

            # serializar os dados
            serializer = ExpenseSerializer(all_expenses, many=True)

            month_names = {
                1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 
                5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 
                9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
            }

            return Response({
                "expenses": serializer.data,
                "count": len(all_expenses),
                "period": f"{month_names[target_month]}/{target_year}"
            }, status=200)

        except ValueError as e:
            return Response({"error": f"Ano inválido: {year}"}, status=400)
        except Exception as e:
            print(f"Erro na view: {e}")
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=500)