from django.contrib import admin
from .models import Transaction, Client


class TransactionAdmin(admin.ModelAdmin):
    # inlines = [
    #     ActStreamInlineAdmin
    # ]
    exclude = ('status',)

admin.site.register(Transaction, TransactionAdmin)


class ClientAdmin(admin.ModelAdmin):
    pass

admin.site.register(Client, ClientAdmin)