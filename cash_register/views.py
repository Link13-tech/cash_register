import os
from datetime import datetime
from decimal import Decimal
from io import BytesIO

import pdfkit
import qrcode
from django.conf import settings
from django.http import HttpResponse
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

            # Путь к директории для сохранения чека
            receipts_dir = settings.MEDIA_ROOT  # Сохраняем в папку media

            # Сохраняем PDF файл
            filename = f"receipt_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
            receipt_path = os.path.join(receipts_dir, filename)
            with open(receipt_path, 'wb') as f:
                f.write(pdf)

            # Генерация QR-кода с полным URL на чек
            receipt_url = f'{settings.SITE_URL}/media/{filename}'
            qr_code = qrcode.make(receipt_url)

            qr_code_image = BytesIO()
            qr_code.save(qr_code_image, 'PNG')
            qr_code_image.seek(0)

            # Путь для сохранения QR-кода в папку media
            qr_code_filename = f'qr_{filename}.png'
            qr_code_path = os.path.join(settings.MEDIA_ROOT, qr_code_filename)

            # Сохраняем QR-код в файл
            with open(qr_code_path, 'wb') as f:
                f.write(qr_code_image.getvalue())

            # Возвращаем сам QR-код в качестве изображения в ответе
            return HttpResponse(qr_code_image, content_type="image/png")

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        # Возвращаем сообщение, чтобы использовать POST метод
        return Response({
            "message": "Please use POST method to generate receipt."
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)


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
