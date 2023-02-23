from django.db import models
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests
import mimetypes
from tempfile import NamedTemporaryFile
from urllib.request import urlopen
from django.core.files.base import File as Django_File


class Tariff(models.Model):

    title = models.CharField(
        unique=True,
        max_length=256,
        verbose_name='Название'
    )
    description = models.TextField(
        verbose_name='Описание'
    )
    request_quantity = models.PositiveSmallIntegerField(
        verbose_name='Количество заявок'
    )
    price = models.PositiveBigIntegerField(
        verbose_name='Цена'
    )

    class Meta:
        verbose_name = 'Тариф'
        verbose_name_plural = 'Тарифы'

    def __str__(self):
        return self.title


class Administrator(models.Model):

    full_name = models.CharField(
        max_length=256,
        verbose_name='Полное имя'
    )
    chat_id = models.PositiveBigIntegerField(
        verbose_name='ID чата в ТГ'
    )

    class Meta:
        verbose_name = 'Администратор'
        verbose_name_plural = 'Администраторы'

    def __str__(self):
        return f'{self.full_name}: {self.chat_id}'


class Client(models.Model):

    chat_id = models.PositiveBigIntegerField(
        verbose_name='ID чата в ТГ'
    )
    tariff = models.ForeignKey(
        null=True,
        to=Tariff,
        on_delete=models.SET_NULL,
        verbose_name='Тариф'
    )
    requests_left = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Кол-во оставшихся запросов'
    )
    end = models.DateField(
        null=True,
        blank=True,
        default=datetime.today() + relativedelta(months=1),
        verbose_name='Дата конца тарифа'
    )

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'

    def __str__(self):
        return f'{self.chat_id} - {self.tariff}'


class Freelancer(models.Model):

    chat_id = models.PositiveBigIntegerField(
        verbose_name='ID чата в ТГ'
    )

    class Meta:
        verbose_name = 'Подрядчик'
        verbose_name_plural = 'Подрядчики'

    def __str__(self):
        return str(self.chat_id)


class Order(models.Model):

    title = models.CharField(
        max_length=256,
        verbose_name='Название'
    )
    description = models.TextField(
        verbose_name='Описание'
    )
    client = models.ForeignKey(
        to=Client,
        on_delete=models.CASCADE,
        verbose_name='Клиент'
    )
    freelancer = models.ForeignKey(
        blank=True,
        null=True,
        to=Freelancer,
        on_delete=models.SET_NULL,
        verbose_name='Подрядчик'
    )
    published = models.DateTimeField(
        default=datetime.now(),
        verbose_name='Опубликован'
    )
    put_into_action = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Взят в работу'
    )
    finished = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Завершен'
    )

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'{self.title}'


class File(models.Model):
    file = models.FileField(
        verbose_name='Файл'
    )
    file_url = models.URLField(
        blank=True,
        null=True,
        verbose_name='Ссылка на файл'
    )
    order = models.ForeignKey(
        to=Order,
        on_delete=models.CASCADE,
        verbose_name='Заказ'
    )

    def get_file_from_url(self):
        response = requests.get(self.file_url)
        response.raise_for_status()
        content_type = response.headers['content-type']
        extension = mimetypes.guess_extension(content_type)

        file_tmp = NamedTemporaryFile(delete=True)
        file_tmp.write(response.content)
        file = Django_File(file_tmp)
        self.file.save(f'{self.order.title}{extension}', file)

    class Meta:
        verbose_name = 'Файл к заказу'
        verbose_name_plural = 'Файлы к заказу'

    def __str__(self):
        return self.file.name
