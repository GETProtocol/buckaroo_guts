from django.contrib import admin
from utils.admin import ActStreamInlineAdmin

from .models import Transaction, Client


class TransactionAdmin(admin.ModelAdmin):
    inlines = [
        ActStreamInlineAdmin
    ]

admin.site.register(Transaction, TransactionAdmin)


class ClientAdmin(admin.ModelAdmin):
    pass

admin.site.register(Client, ClientAdmin)