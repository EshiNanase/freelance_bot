from django.contrib import admin
from telegram_bot.models import Administrator, Client, Freelancer, Tariff, Order, File


class FileTabularInLine(admin.TabularInline):

    model = File
    extra = 0


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
    inlines = [
        FileTabularInLine
    ]
    readonly_fields = ('id',)
    fields = ['title', 'id', 'description', 'client', 'freelancer', 'published', 'put_into_action', 'finished']
