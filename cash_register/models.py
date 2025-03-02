from django.db import models


class Item(models.Model):
    title = models.CharField(max_length=255, verbose_name="Наименование")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")

    def __str__(self):
        return self.title
