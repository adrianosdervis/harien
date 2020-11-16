import json
import datetime
import stripe
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.views import generic
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.mail import send_mail, send_mass_mail
from .utils import get_or_set_order_session
from .models import OrderItem, Address, Payment, Order, StripePayment, BankPayment, DoorPayment
from .forms import AddressForm, StripePaymentForm, BankForm, DoorForm

stripe.api_key = settings.STRIPE_SECRET_KEY


class CartView(generic.TemplateView):
    template_name = 'cart/cart.html'

    def get_context_data(self, **kwargs):
        context = super(CartView, self).get_context_data(**kwargs)
        context['order'] = get_or_set_order_session(self.request)
        return context


class IncreaseQuantityView(generic.View):
    def get(self, request, *args, **kwargs):
        order_item = get_object_or_404(OrderItem, id=kwargs['pk'])
        order_item.quantity += 1
        order_item.save()
        return redirect('cart')


class DecreaseQuantityView(generic.View):
    def get(self, request, *args, **kwargs):
        order_item = get_object_or_404(OrderItem, id=kwargs['pk'])
        if order_item.quantity <= 1:
            order_item.delete()
        else:
            order_item.quantity -= 1
            order_item.save()
        return redirect('cart')


class RemoveFromCartView(generic.View):
    def get(self, request, *args, **kwargs):
        order_item = get_object_or_404(OrderItem, id=kwargs['pk'])
        order_item.delete()
        return redirect('cart')


class CheckoutView(LoginRequiredMixin, generic.FormView):
    template_name = 'cart/checkout.html'
    form_class = AddressForm

    def get_success_url(self):
        return reverse('payment')

    def form_valid(self, form):
        order = get_or_set_order_session(self.request)
        selected_shipping_address = form.cleaned_data.get(
            'selected_shipping_address')
        selected_billing_address = form.cleaned_data.get(
            'selected_billing_address')

        if selected_shipping_address:
            order.shipping_address = selected_shipping_address
        else:
            address = Address.objects.create(
                address_type='S',
                user=self.request.user,
                address_line_1=form.cleaned_data['shipping_address_line_1'],
                address_line_2=form.cleaned_data['shipping_address_line_2'],
                zip_code=form.cleaned_data['shipping_zip_code'],
                city=form.cleaned_data['shipping_city'],
            )
            order.shipping_address = address

        if selected_billing_address:
            order.billing_address = selected_billing_address
        else:
            address = Address.objects.create(
                address_type='B',
                user=self.request.user,
                address_line_1=form.cleaned_data['billing_address_line_1'],
                address_line_2=form.cleaned_data['billing_address_line_2'],
                zip_code=form.cleaned_data['billing_zip_code'],
                city=form.cleaned_data['billing_city'],
            )
            order.billing_address = address

        order.save()

        messages.info(
            self.request, 'You have successfully added your addresses')
        return super(CheckoutView, self).form_valid(form)

    def get_form_kwargs(self):
        kwargs = super(CheckoutView, self).get_form_kwargs()
        kwargs['user_id'] = self.request.user.id
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(CheckoutView, self).get_context_data(**kwargs)
        context['order'] = get_or_set_order_session(self.request)
        return context


class PaymentView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'cart/payment.html'

    def get_context_data(self, **kwargs):
        context = super(PaymentView, self).get_context_data(**kwargs)
        # context['PAYPAL_CLIENT_ID'] = settings.PAYPAL_CLIENT_ID
        context['order'] = get_or_set_order_session(self.request)
        # context['CALLBACK_URL'] = self.request.build_absolute_uri(
        #     reverse('thanks'))
        return context


class BankPaymentView(LoginRequiredMixin, generic.FormView):
    template_name = 'cart/bank-payment.html'
    form_class = BankForm

    def form_valid(self, form):
        bank_id = form.cleaned_data['bank_transfer_id']
        order = get_or_set_order_session(self.request)
        print(order)
        order.ordered = True
        order.payment_method = 'Bank'
        order.ordered_date = timezone.now()
        order.save()

        bank_transaction, created = BankPayment.objects.get_or_create(
            order=order)
        bank_transaction.bank_id = bank_id
        bank_transaction.successful = True
        bank_transaction.amount = int(order.get_total())
        bank_transaction.save()

        return redirect('bank-thanks')

    def get_context_data(self, **kwargs):
        context = super(BankPaymentView, self).get_context_data(**kwargs)
        context['order'] = get_or_set_order_session(self.request)
        return context


class DoorPaymentView(LoginRequiredMixin, generic.FormView):
    template_name = 'cart/door-payment.html'
    form_class = DoorForm

    def form_valid(self, form):
        order = get_or_set_order_session(self.request)
        print(order)
        order.ordered = True
        order.payment_method = 'Door'
        order.ordered_date = timezone.now()
        order.save()

        door_transaction, created = DoorPayment.objects.get_or_create(
            order=order)
        door_transaction.successful = True
        door_transaction.amount = int(order.get_total())
        door_transaction.save()

        return redirect('door-thanks')

    def get_context_data(self, **kwargs):
        context = super(DoorPaymentView, self).get_context_data(**kwargs)
        context['order'] = get_or_set_order_session(self.request)
        return context


class StripePaymentView(LoginRequiredMixin, generic.FormView):
    template_name = 'cart/stripe-payment.html'
    form_class = StripePaymentForm

    def form_valid(self, form):
        payment_method = form.cleaned_data['selectedCard']
        print(payment_method)
        if payment_method != 'newCard':
            try:
                order = get_or_set_order_session(self.request)
                payment_intent = stripe.PaymentIntent.create(
                    amount=int(order.get_total() * 100),
                    currency='eur',
                    customer=self.request.user.customer.stripe_customer_id,
                    payment_method=payment_method,
                    off_session=True,
                    confirm=True,
                )
                payment_record, created = StripePayment.objects.get_or_create(
                    order=order)
                payment_record.payment_intent_id = payment_intent['id']
                payment_record.amount = int(order.get_total())
                payment_record.save()

            except stripe.error.CardError as e:
                err = e.error
                # Error code will be authentication_required if authentication is needed
                print("Code is: %s" % err.code)
                payment_intent_id = err.payment_intent['id']
                payment_intent = stripe.PaymentIntent.retrieve(
                    payment_intent_id)
                messages.warning(self.request, '"Code is: %s" % err.code')
        return redirect('stripe-thanks')

    def get_context_data(self, **kwargs):
        user = self.request.user
        if not user.customer.stripe_customer_id:
            stripe_customer = stripe.Customer.create(email=user.email)
            user.customer.stripe_customer_id = stripe_customer['id']
            user.customer.save()

        order = get_or_set_order_session(self.request)
        payment_intent = stripe.PaymentIntent.create(
            amount=int(order.get_total() * 100),
            currency='eur',
            customer=user.customer.stripe_customer_id,
        )

        payment_record, created = StripePayment.objects.get_or_create(
            order=order)
        payment_record.payment_intent_id = payment_intent['id']
        payment_record.amount = int(order.get_total())
        payment_record.save()

        cards = stripe.PaymentMethod.list(
            customer=user.customer.stripe_customer_id,
            type="card",
        )
        payment_methods = []
        for card in cards:
            payment_methods.append({
                'last4': card['card']['last4'],
                'brand': card['card']['brand'],
                'exp_month': card['card']['exp_month'],
                'exp_year': card['card']['exp_year'],
                'pm_id': card['id'],
            })
        # print(payment_methods)
        context = super(StripePaymentView, self).get_context_data(**kwargs)
        context['STRIPE_PUBLIC_KEY'] = settings.STRIPE_PUBLIC_KEY
        context['client_secret'] = payment_intent['client_secret']
        context['payment_methods'] = payment_methods
        return context


class ConfirmOrderView(generic.View):
    def post(self, request, *args, **kwargs):
        order = get_or_set_order_session(request)
        body = json.loads(request.body)
        payment = Payment.objects.create(
            order=order,
            successful=True,
            raw_response=json.dumps(body),
            amount=float(body['purchase_units'][0]['amount']['value']),
            payment_method='Card'
        )
        order.ordered = True
        order.ordered_date = datetime.date.today()
        order.save()
        return JsonResponse({'data': 'Success'})


class BankThankYouView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'cart/thanks.html'

    def get_context_data(self, **kwargs):
        context = super(BankThankYouView, self).get_context_data(**kwargs)
        order = Order.objects.filter(
            user=self.request.user, ordered=True).last()
        payment = BankPayment.objects.get(order=order)
        context['order'] = order
        subject1 = f'Harien - New order - {order}'
        subject2 = f'Harien - Order - {order}'
        message1 = f"""
            You have a new order from {self.request.user.username}, {self.request.user.email}
            
            Order: {order}
            Amount: {payment.amount}
            Payment method: Bank payment
            Billing address: {order.billing_address}
            Shipping address: {order.shipping_address}

            Go to site --> staff section to check it out
            """
        message2 = f"""
            {self.request.user.username}, thank you for your order!
            
            Order: {order}
            Amount: {payment.amount}
            Payment method: Bank payment
            Billing address: {order.billing_address}
            Shipping address: {order.shipping_address}
            """
        datatuple = (
            (subject1, message1, settings.EMAIL_HOST_USER,
             ['adrianosdervis@gmail.com']),
            (subject2, message2, settings.EMAIL_HOST_USER,
             [self.request.user.email]),
        )
        send_mass_mail(datatuple)
        return context


class DoorThankYouView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'cart/thanks.html'

    def get_context_data(self, **kwargs):
        context = super(DoorThankYouView, self).get_context_data(**kwargs)
        order = Order.objects.filter(
            user=self.request.user, ordered=True).last()
        payment = DoorPayment.objects.get(order=order)
        context['order'] = order
        subject1 = f'Harien - New order - {order}'
        subject2 = f'Harien - Order - {order}'
        message1 = f"""
            You have a new order from {self.request.user.username}, {self.request.user.email}
            
            Order: {order}
            Amount: {payment.amount}
            Payment method: Payment when received
            Billing address: {order.billing_address}
            Shipping address: {order.shipping_address}

            Go to site --> staff section to check it out
            """
        message2 = f"""
            {self.request.user.username}, thank you for your order!
            
            Order: {order}
            Amount: {payment.amount}
            Payment method: Payment when received
            Billing address: {order.billing_address}
            Shipping address: {order.shipping_address}
            """
        datatuple = (
            (subject1, message1, settings.EMAIL_HOST_USER,
             ['adrianosdervis@gmail.com']),
            (subject2, message2, settings.EMAIL_HOST_USER,
             [self.request.user.email]),
        )
        send_mass_mail(datatuple)
        return context


class StripeThankYouView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'cart/stripe-thanks.html'

    def get_context_data(self, **kwargs):
        context = super(StripeThankYouView, self).get_context_data(**kwargs)
        order = get_or_set_order_session(self.request)
        payment = StripePayment.objects.get(order=order)
        context['order'] = order
        subject1 = f'Harien - New order - {order}'
        subject2 = f'Harien - Order - {order}'
        message1 = f"""
            You have a new order from {self.request.user.username}, {self.request.user.email}
            
            Order: {order}
            Amount: {payment.amount}
            Payment method: Card payment
            Billing address: {order.billing_address}
            Shipping address: {order.shipping_address}

            Go to site --> staff section to check it out
            """
        message2 = f"""
            {self.request.user.username}, thank you for your order!
            
            Order: {order}
            Amount: {payment.amount}
            Payment method: Card Payment
            Billing address: {order.billing_address}
            Shipping address: {order.shipping_address}
            """
        datatuple = (
            (subject1, message1, settings.EMAIL_HOST_USER,
             ['adrianosdervis@gmail.com']),
            (subject2, message2, settings.EMAIL_HOST_USER,
             [self.request.user.email]),
        )
        send_mass_mail(datatuple)
        return context


class OrderDetailView(LoginRequiredMixin, generic.DetailView):
    template_name = 'cart/order.html'
    queryset = Order.objects.all()
    context_object_name = 'order'


# If you are testing your webhook locally with the Stripe CLI you
# can find the endpoint's secret by running `stripe listen`
# Otherwise, find your endpoint's secret in your webhook settings in the Developer Dashboard
@csrf_exempt
def stripe_webhook_view(request):
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the event
    if event.type == 'payment_intent.succeeded':
        payment_intent = event.data.object  # contains a stripe.PaymentIntent
        stripe_payment = StripePayment.objects.get(
            payment_intent_id=payment_intent['id'],
        )
        stripe_payment.successful = True
        stripe_payment.save()
        order = stripe_payment.order
        order.ordered = True
        order.payment_method = 'Card'
        order.ordered_date = timezone.now()
        order.save()
    else:
        print('Unhandled event type {}'.format(event.type))

    return HttpResponse(status=200)
