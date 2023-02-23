import stripe
from freelance.settings import STRIPE_SECRET_KEY
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from telegram_bot.models import Client, Tariff
from django.http.response import HttpResponse
from http import HTTPStatus
from django.shortcuts import get_object_or_404
from datetime import datetime
from dateutil.relativedelta import relativedelta

stripe.api_key = STRIPE_SECRET_KEY


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


def send_payment_link(chat_id, tariff):

    stripe_id = get_object_or_404(Tariff, title=tariff).stripe_id

    checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                        # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                        'price': stripe_id,
                        'quantity': 1,
                    },
                ],
                metadata={'chat_id': chat_id, 'tariff': tariff},
                mode='payment',
                success_url='https://www.youtube.com/watch?v=cuX5QQXbLDQ'
            )
    return checkout_session.url
