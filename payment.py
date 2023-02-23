import stripe


def send_payment_link(chat_id, tariff, stripe_id):

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
