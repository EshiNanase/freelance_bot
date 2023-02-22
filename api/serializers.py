from rest_framework import serializers
from telegram_bot.models import Client, Order, Freelancer, Tariff


class TariffSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tariff
        fields = '__all__'


class ClientSerializer(serializers.ModelSerializer):

    tariff = TariffSerializer()

    class Meta:
        model = Client
        fields = ['chat_id', 'tariff']


class FreelancerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Freelancer
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):

    client = ClientSerializer()

    class Meta:
        model = Order
        fields = '__all__'
