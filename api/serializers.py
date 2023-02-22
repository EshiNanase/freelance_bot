from rest_framework.serializers import ModelSerializer
from telegram_bot.models import Client


class ClientSerializer(ModelSerializer):

    class Meta:
        model = Client
        fields = ['chat_id', 'tariff']
