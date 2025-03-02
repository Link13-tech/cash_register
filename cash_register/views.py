import base64
import os
from datetime import datetime
from decimal import Decimal

import pdfkit
import qrcode
from django.conf import settings
from django.http import HttpResponse, FileResponse
from django.views import View
from jinja2 import FileSystemLoader, Environment
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Item
from .serializers import ItemSerializer, GenerateReceiptSerializer


# API для просмотра и создания товаров
class ItemListCreateView(generics.ListCreateAPIView):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer


class GenerateReceiptView(APIView):
    def post(self, request, *args, **kwargs):
        # Валидируем данные с помощью сериализатора
        serializer = GenerateReceiptSerializer(data=request.data)

        if serializer.is_valid():
            # Получаем список ID товаров из запроса
            item_ids = serializer.validated_data['item_ids']
            items = Item.objects.filter(id__in=item_ids)

            # Получаем шаблон чека через Jinja2
            env = Environment(loader=FileSystemLoader(os.path.join(settings.BASE_DIR, 'cash_register', 'templates')))
            template = env.get_template('receipt_template.html')

            # Формируем данные для шаблона
            total_price = sum(Decimal(item.price) * item.quantity for item in items)
            created_at = datetime.now().strftime('%d.%m.%Y %H:%M')

            context = {
                'items': items,
                'total_price': total_price,
                'created_at': created_at
            }

            # Рендерим HTML-шаблон с подставленными данными
            html = template.render(context)

            # Генерируем PDF из HTML
            pdf = pdfkit.from_string(html, False)

            # Директория для сохранения чеков
            receipts_dir = settings.MEDIA_ROOT

            # Сохраняем PDF файл
            filename = f"receipt_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
            receipt_path = os.path.join(receipts_dir, filename)
            with open(receipt_path, 'wb') as f:
                f.write(pdf)

            qr_code_filename = f"qr_{filename}.png"
            qr_code_path = os.path.join(receipts_dir, qr_code_filename)

            # Генерация QR-кода с ссылкой на чек
            receipt_url = f"{settings.SITE_URL}{settings.MEDIA_URL}{filename}"
            qr_code = qrcode.make(receipt_url)
            qr_code.save(qr_code_path)

            return FileResponse(open(qr_code_path, 'rb'), content_type="image/png")

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ServeReceiptFile(View):
    def get(self, request, filename):
        # Путь к файлу
        file_path = os.path.join(settings.MEDIA_ROOT, filename)

        # Проверяем, существует ли файл
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename={filename}'
                return response

        # Если файл не найден, возвращаем ошибку
        return HttpResponse(status=404)
