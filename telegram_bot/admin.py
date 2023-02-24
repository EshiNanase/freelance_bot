from django.contrib import admin
from telegram_bot.models import Administrator, Client, Freelancer, Tariff, Order


@admin.register(Administrator)
class AdministratorAdmin(admin.ModelAdmin):
    pass


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    pass


@admin.register(Freelancer)
class FreelancerAdmin(admin.ModelAdmin):
    pass


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    pass


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
