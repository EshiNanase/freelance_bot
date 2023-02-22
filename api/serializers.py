from rest_framework import serializers
from telegram_bot.models import Client, Order


class ClientSerializer(serializers.ModelSerializer):

    tariff = serializers.CharField()

    class Meta:
        model = Client
        fields = ['chat_id', 'tariff']


class OrderSerializer(serializers.ModelSerializer):

    client = ClientSerializer()

    class Meta:
        model = Order
        fields = '__all__'
