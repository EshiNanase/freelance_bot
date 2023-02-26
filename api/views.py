from telegram_bot.models import Client, Tariff, Order, Freelancer
from django.shortcuts import get_object_or_404
from http import HTTPStatus
from rest_framework.response import Response
from rest_framework.decorators import api_view
from datetime import datetime
from dateutil.relativedelta import relativedelta
from api.serializers import ClientSerializer, OrderSerializer, TariffSerializer, FreelancerSerializer, OrderCreateSerializer, OrderAppointFreelancerSerializer, OrderFinishSerializer, ContactOtherSideSerializer
from drf_spectacular.utils import extend_schema
from django.db import transaction
from rest_framework.pagination import PageNumberPagination
import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http.response import HttpResponse

stripe.api_key = settings.STRIPE_SECRET_KEY


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

    order = Order.objects.get(id=order_id)

    serializer = OrderSerializer(order)
    return Response(
        data=serializer.data,
        status=HTTPStatus.OK
    )


@extend_schema(request=ClientSerializer, description='Создание клиента')
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

    orders = Order.objects.all()

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

    serializer = OrderCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.data

    client = get_object_or_404(Client, chat_id=data['chat_id'])
    if client.requests_left - 1 < 0:
        return Response(data={'error': 'max requests exceeded'}, status=HTTPStatus.BAD_REQUEST)
    client.requests_left -= 1
    client.save()

    order = Order.objects.create(
        title=data['title'],
        description=data['description'],
        client=client
    )
    if data.get('files'):
        for file in data['files']:
            order.files.append(file)
            order.save()

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
    orders = Order.objects.filter(freelancer=freelancer, finished__isnull=True)

    serializer = OrderSerializer(orders, many=True)

    return Response(
        data=serializer.data,
        status=HTTPStatus.OK
    )


@extend_schema(description='Отображение заказов определенного клиента')
@api_view(['GET'])
def get_client_orders(request, chat_id) -> Response:

    client = get_object_or_404(Client, chat_id=chat_id)
    orders = Order.objects.filter(client=client)

    serializer = OrderSerializer(orders, many=True)

    return Response(
        data=serializer.data,
        status=HTTPStatus.OK
    )


# TODO Спросить про алгоритм фильтрации заказов
@extend_schema(description='Отображение пяти заказов, порядок с VIP\'а')
@api_view(['GET'])
def find_orders(request) -> Response:

    paginator = PageNumberPagination()
    paginator.page_size = 5
    orders = Order.objects.filter(freelancer__isnull=True).all().order_by('-client__tariff')
    orders_result = paginator.paginate_queryset(orders, request)
    serializer = OrderSerializer(orders_result, many=True)

    return paginator.get_paginated_response(serializer.data)


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
# TODO Спросить про возможность "закрепить подрядчика за собой"


@extend_schema(request=ContactOtherSideSerializer, description='Пообщаться с другой стороной')
@api_view(['POST'])
def contact_other_side(request) -> Response:

    serializer = ContactOtherSideSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.data

    order = get_object_or_404(Order, id=data['order_id'])
    order.dialogue += f'{data["message"]}\n'
    order.save()

    return Response(
        data=serializer.data,
        status=HTTPStatus.OK
    )


@csrf_exempt
def stripe_webhook_view(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = stripe.Webhook.construct_event(
        payload, sig_header, settings.STRIPE_WEBHOOK_KEY
      )

    if event['type'] == 'checkout.session.completed':
        session = stripe.checkout.Session.retrieve(
            event['data']['object']['id'],
            expand=['line_items'],
        )

        tariff = get_object_or_404(Tariff, title=session.metadata.tariff)
        updated_values = {
            'tariff': tariff,
            'requests_left': tariff.request_quantity
        }

        client, created = Client.objects.update_or_create(
            chat_id=session.metadata.chat_id,
            defaults=updated_values
        )
        if not created:
            client.end = datetime.today() + relativedelta(months=1)
            client.save()

    return HttpResponse(status=HTTPStatus.OK)
