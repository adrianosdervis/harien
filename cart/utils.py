from .models import Order
from django.utils import timezone


def get_or_set_order_session(request):
    order_id = request.session.get('order_id', None)

    if order_id is None:
        order = Order()
        order.ordered_date = timezone.now()
        order.save()
        request.session['order_id'] = order.id
    else:
        try:
            order = Order.objects.get(id=order_id, ordered=False)
        except Order.DoesNotExist:
            order = Order()
            order.ordered_date = timezone.now()
            order.save()
            request.session['order_id'] = order.id

    if request.user.is_authenticated and order.user is None:
        order.user = request.user
        order.ordered_date = timezone.now()
        order.save()

    return order
