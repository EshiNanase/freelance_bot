from telegram_bot.models import Client, Tariff, Order, Freelancer, File
from django.shortcuts import get_object_or_404
from http import HTTPStatus
from rest_framework.response import Response
from rest_framework.decorators import api_view
from datetime import datetime
from dateutil.relativedelta import relativedelta
from api.serializers import ClientSerializer, OrderSerializer, TariffSerializer, FreelancerSerializer, OrderCreateSerializer, OrderAppointFreelancerSerializer, OrderFinishSerializer
from drf_spectacular.utils import extend_schema
from django.db import transaction


@extend_schema(description='Проверка на клиента')
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


@extend_schema(description='Проверка на фрилансера')
@api_view(['GET'])
def get_freelancer(request, chat_id) -> Response:
    freelancer = get_object_or_404(Freelancer, chat_id=chat_id)
    response = {
        'chat_id': freelancer.chat_id,
    }
    return Response(
        data=response,
        status=HTTPStatus.OK
    )


@extend_schema(description='Список всех тарифов')
@api_view(['GET'])
def get_tariffs(request) -> Response:
    tariffs = list(Tariff.objects.all())
    response = {'tariffs': [tariff.title for tariff in tariffs]}
    return Response(
        data=response,
        status=HTTPStatus.OK
    )


@extend_schema(description='Детальное отображение тарифа (тариф должен быть с большой буквы)')
@api_view(['GET'])
def get_detailed_tariff(request, tariff_name) -> Response:
    tariff = get_object_or_404(Tariff, title=tariff_name)
    serializer = TariffSerializer(tariff)
    return Response(
        data=serializer.data,
        status=HTTPStatus.OK
    )


@extend_schema(description='Детальное отображение заказа')
@api_view(['GET'])
def get_detailed_order(request, order_id) -> Response:
    order = get_object_or_404(Order, id=order_id)
    serializer = OrderSerializer(order)
    return Response(
        data=serializer.data,
        status=HTTPStatus.OK
    )


@extend_schema(request=ClientSerializer, description='Создание фрилансера')
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


@extend_schema(request=FreelancerSerializer, description='Создание фрилансера')
@api_view(['POST'])
def create_freelancer(request) -> Response:

    data = request.data

    serializer = FreelancerSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    Freelancer.objects.create(chat_id=data['chat_id'])

    return Response(data=serializer.data, status=HTTPStatus.OK)


@extend_schema(description='Отображение всех заказов')
@api_view(['GET'])
def get_orders(request) -> Response:

    orders = list(Order.objects.all())
    serializer = OrderSerializer(orders, many=True)
    response = serializer.data

    return Response(
        data=response,
        status=HTTPStatus.OK
    )


@transaction.atomic
@extend_schema(request=OrderCreateSerializer, description='Создание заказа')
@api_view(['POST'])
def create_order(request) -> Response:

    data = request.data
    serializer = OrderCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    client = get_object_or_404(Client, chat_id=data['chat_id'])
    client.requests_left -= 1
    client.save()

    order = Order.objects.create(
        title=data['title'],
        description=data['description'],
        client=client
    )

    if data.get('files'):
        for file in data['files']:
            file, created = File.objects.get_or_create(
                order=order,
                file_url=file,
            )
            file.get_file_from_url()
            file.save()

    return Response(
        data=serializer.data,
        status=HTTPStatus.OK
    )


@extend_schema(request=OrderAppointFreelancerSerializer, description='Назначение фрилансера на заказ')
@api_view(['POST'])
def appoint_freelancer(request) -> Response:

    data = request.data
    serializer = OrderAppointFreelancerSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    freelancer = get_object_or_404(Freelancer, chat_id=data['chat_id'])
    Order.objects.filter(id=data['order_id']).update(
        freelancer=freelancer,
        put_into_action=datetime.today() + relativedelta(months=1)
    )

    return Response(
        data=serializer.data,
        status=HTTPStatus.OK
    )


@extend_schema(description='Отображение заказов определенного фрилансера')
@api_view(['GET'])
def get_freelancer_orders(request, chat_id) -> Response:

    freelancer = get_object_or_404(Freelancer, chat_id=chat_id)
    orders = list(Order.objects.filter(freelancer=freelancer))
    serializer = OrderSerializer(orders, many=True)

    return Response(
        data=serializer.data,
        status=HTTPStatus.OK
    )


@extend_schema(description='Отображение заказов определенного клиента')
@api_view(['GET'])
def get_client_orders(request, chat_id) -> Response:

    client = get_object_or_404(Client, chat_id=chat_id)
    orders = list(Order.objects.filter(client=client))
    serializer = OrderSerializer(orders, many=True)

    return Response(
        data=serializer.data,
        status=HTTPStatus.OK
    )


# TODO Спросить про алгоритм фильтрации заказов
@extend_schema(description='Отображение пяти заказов, порядок с VIP\'а')
@api_view(['GET'])
def find_orders(request) -> Response:

    orders = list(Order.objects.filter(freelancer__isnull=True).order_by('-client__tariff'))[:5]
    serializer = OrderSerializer(orders, many=True)

    return Response(
        data=serializer.data,
        status=HTTPStatus.OK
    )


# TODO Спросить про критерии завершенного заказа
@extend_schema(request=OrderFinishSerializer, description='Завершить заказ')
@api_view(['POST'])
def finish_order(request) -> Response:

    data = request.data
    serializer = OrderFinishSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    Order.objects.filter(id=data['order_id']).update(
        finished=datetime.today() + relativedelta(months=1)
    )

    return Response(
        data=serializer.data,
        status=HTTPStatus.OK
    )

# TODO Спросить менеджмент заказов со стороны клиента и фрилансера
