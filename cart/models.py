from django.db import models
from django.contrib.auth import get_user_model
from shop.models import Product, ColourVariation, SizeVariation

User = get_user_model()


class Address(models.Model):
    ADDRESS_CHOICES = (
        ('B', 'Billing'),
        ('S', 'Shipping'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address_line_1 = models.CharField(max_length=150)
    address_line_2 = models.CharField(max_length=150)
    city = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.address_line_1}, {self.address_line_2}, {self.city}, {self.zip_code}'

    class Meta:
        verbose_name_plural = 'Addresses'


class OrderItem(models.Model):
    order = models.ForeignKey(
        'Order', related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    colour = models.ForeignKey(
        ColourVariation, on_delete=models.CASCADE)
    size = models.ForeignKey(
        SizeVariation, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.quantity} x {self.product.name}'

    def get_total_item_price(self):
        return self.quantity * self.product.price


class Order(models.Model):
    user = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField(blank=True, null=True)
    ordered = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=20, choices=(
        ('Card', 'Card'),
        ('Bank', 'Bank'),
        ('Door', 'Door'),
    ), blank=True)
    billing_address = models.ForeignKey(
        Address, related_name='billing_address', blank=True, null=True, on_delete=models.SET_NULL)
    shipping_address = models.ForeignKey(
        Address, related_name='shipping_address', blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.reference_number

    @property
    def reference_number(self):
        return f'ORDER-{self.pk}'

    def get_subtotal(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_total_item_price()
        return total

    def get_total(self):
        subtotal = self.get_subtotal()
        # subtrack discounts, add tax, add delivery
        # total = subtotal - discounts + tax + delivery
        total = subtotal
        return total


class Payment(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=(
        ('Card', 'Card'),
        ('Bank', 'Bank'),
        ('Door', 'Door'),
    ))
    timestamp = models.DateTimeField(auto_now_add=True)
    successful = models.BooleanField(default=False)
    amount = models.FloatField()
    raw_response = models.TextField()

    def __str__(self):
        return self.reference_number

    @property
    def reference_number(self):
        return f'PAYMENT-{self.order}-{self.pk}'


class StripePayment(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='stripe_payments')
    payment_intent_id = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    successful = models.BooleanField(default=False)
    amount = models.FloatField(default=0)

    def __str__(self):
        return self.reference_number

    @property
    def reference_number(self):
        return f'STRIPE-PAYMENT-{self.order}-{self.pk}'


class BankPayment(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='bank_payments')
    bank_id = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)
    successful = models.BooleanField(default=False)
    amount = models.FloatField(default=0)

    def __str__(self):
        return self.reference_number

    @property
    def reference_number(self):
        return f'BANK-PAYMENT-{self.order}-{self.pk}'


class DoorPayment(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='door_payments')
    timestamp = models.DateTimeField(auto_now_add=True)
    successful = models.BooleanField(default=False)
    amount = models.FloatField(default=0)

    def __str__(self):
        return self.reference_number

    @property
    def reference_number(self):
        return f'DOOR-PAYMENT-{self.order}-{self.pk}'
