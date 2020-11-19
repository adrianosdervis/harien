from .models import Order
from django.utils import timezone


def get_or_set_order_session(request):
    order_id = request.session.get('order_id', None)
    print(f'Getting order id: {order_id}. The user is {request.user}')

    if order_id is None and not request.user.is_anonymous:
        print(f'Order id is None and user is {request.user}')
        order = Order()
        order.ordered_date = timezone.now()
        order.save()
        print(f'Order is none. New order: {order} with user: {request.user}')
        request.session['order_id'] = order.id
    else:
        try:
            order = Order.objects.get(id=order_id, ordered=False)
            print(f'Found an order: {order}')
        except Order.DoesNotExist:
            print(f'Order id is still none. User is {request.user}')
            order = Order()
            order.ordered_date = timezone.now()
            order.save()
            print(f'Order is still none. New order: {order}')
            request.session['order_id'] = order.id

    if request.user.is_authenticated and order.user is None:
        order.user = request.user
        order.ordered_date = timezone.now()
        order.save()
        print(f'{order} with user {request.user}')

    return order
