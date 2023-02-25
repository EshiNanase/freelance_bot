from rest_framework import serializers
from telegram_bot.models import Client, Order, Freelancer, Tariff


class TariffSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tariff
        fields = '__all__'


class ClientSerializer(serializers.ModelSerializer):

    tariff = serializers.CharField()

    class Meta:
        model = Client
        fields = ['chat_id', 'tariff']


class FreelancerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Freelancer
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):

    client = ClientSerializer()
    freelancer = FreelancerSerializer()

    class Meta:
        model = Order
        fields = '__all__'


class OrderCreateSerializer(serializers.Serializer):

    title = serializers.CharField()
    description = serializers.CharField()
    chat_id = serializers.IntegerField()
    files = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )


class OrderAppointFreelancerSerializer(serializers.Serializer):

    chat_id = serializers.IntegerField()
    order_id = serializers.IntegerField()


class OrderFinishSerializer(serializers.Serializer):

    order_id = serializers.IntegerField()


class ContactOtherSideSerializer(serializers.Serializer):

    order_id = serializers.IntegerField()
    message = serializers.CharField()
