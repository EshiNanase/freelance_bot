import stripe
import requests
# FIXME
from freelance import settings
stripe.api_key = settings.STRIPE_SECRET_KEY



def send_payment_link(chat_id, tariff):

    url = f'{settings.API_URL}/api/tariff/{tariff}'
    response = requests.get(url)
    response.raise_for_status()
    stripe_id = response.json()['stripe_id']

    checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                        'price': stripe_id,
                        'quantity': 1,
                    },
                ],
                metadata={'chat_id': chat_id, 'tariff': tariff},
                mode='payment',
                success_url='https://www.youtube.com/watch?v=cuX5QQXbLDQ'
            )
    return checkout_session.url
