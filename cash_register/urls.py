from django.urls import path
from .views import ItemListCreateView, GenerateReceiptView, ServeReceiptFile

urlpatterns = [
    path('items/', ItemListCreateView.as_view(), name='item-list-create'),
    path('generate_receipt/', GenerateReceiptView.as_view(), name='generate-receipt'),
    path('media/<str:filename>', ServeReceiptFile.as_view(), name='serve-receipt'),
]
