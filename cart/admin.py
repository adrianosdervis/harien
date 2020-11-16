from django.contrib import admin
from .models import Order, OrderItem, Address, Payment, StripePayment, BankPayment, DoorPayment

admin.site.register(Order)
admin.site.register(OrderItem)


class AddressAdmin(admin.ModelAdmin):
    list_display = ['address_line_1', 'address_line_2',
                    'city', 'zip_code', 'address_type']


admin.site.register(Address, AddressAdmin)
admin.site.register(Payment)
admin.site.register(StripePayment)
admin.site.register(BankPayment)
admin.site.register(DoorPayment)
