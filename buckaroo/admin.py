from django.contrib import admin
from utils.admin import ActStreamInlineAdmin

from .models import Transaction


class TransactionAdmin(admin.ModelAdmin):
    inlines = [
        ActStreamInlineAdmin
    ]

admin.site.register(Transaction, TransactionAdmin)
