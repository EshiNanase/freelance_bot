from telegram_bot.models import Client, Tariff, Order
from django.shortcuts import get_object_or_404
from http import HTTPStatus
from rest_framework.response import Response
from rest_framework.decorators import api_view
from datetime import datetime
from dateutil.relativedelta import relativedelta
from api.serializers import ClientSerializer, OrderSerializer


@api_view(['GET'])
def get_client(request, chat_id) -> Response:
    client = get_object_or_404(Client, chat_id=chat_id)
    response = {
        'tariff_title': client.tariff.title,
        'days_left': client.end,
        'requests_left': client.requests_left
    }
    return Response(
        data=response,
        status=HTTPStatus.OK
    )


@api_view(['GET'])
def get_tariffs(request) -> Response:
    tariffs = list(Tariff.objects.all())
    response = {'tariffs': [tariff.title for tariff in tariffs]}
    return Response(
        data=response,
        status=HTTPStatus.OK
    )


@api_view(['GET'])
def get_detailed_tariff(request, tariff_name) -> Response:
    tariff = get_object_or_404(Tariff, title=tariff_name)
    response = {
        'title': tariff.title,
        'request_quantity': tariff.request_quantity,
        'price': tariff.price
    }
    return Response(
        data=response,
        status=HTTPStatus.OK
    )


@api_view(['GET'])
def get_detailed_order(request, order_id) -> Response:
    order = get_object_or_404(Order, id=order_id)
    serializer = OrderSerializer(order)
    return Response(
        data=serializer.data,
        status=HTTPStatus.OK
    )


@api_view(['POST'])
def create_client(request) -> Response:

    data = request.data

    serializer = ClientSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    tariff = get_object_or_404(Tariff, title=data['tariff'])
    updated_values = {
        'tariff': tariff,
        'requests_left': tariff.request_quantity
    }

    client, created = Client.objects.update_or_create(
        chat_id=data['chat_id'],
        defaults=updated_values
    )
    if not created:
        client.end = datetime.today() + relativedelta(months=1)
        client.save()

    return Response(data=serializer.data, status=HTTPStatus.OK)
