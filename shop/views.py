from django.shortcuts import render, get_object_or_404, reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.conf import settings
from django.views import generic
from .models import Category, Product
from cart.models import Order, OrderItem
from .forms import ContactForm
from cart.utils import get_or_set_order_session
from cart.forms import AddToCartForm


class ProfileView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'shop/profile.html'

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        context.update({
            'orders': Order.objects.filter(user=self.request.user, ordered=True).order_by('-ordered_date')
        })
        return context


class ContactView(generic.FormView):
    template_name = 'shop/contact.html'
    form_class = ContactForm

    def get_success_url(self):
        return reverse('contact')

    def form_valid(self, form):
        messages.info(
            self.request, 'Thanks for getting in touch. We have received your message.')
        name = form.cleaned_data.get('name')
        email = form.cleaned_data.get('email')
        message = form.cleaned_data.get('message')

        full_message = f"""
            Εισερχόμενο μήνυμα από {name} - {email}


            {message}
        """

        send_mail(
            subject='Received contact form submission',
            message=full_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['adrianosdervis@gmail.com', ]
        )

        return super(ContactView, self).form_valid(form)


class HomeView(generic.ListView):
    template_name = 'shop/home.html'

    def get_queryset(self):
        qs = Product.objects.all().filter(available=True)
        category = self.request.GET.get('category', None)
        if category:
            qs = qs.filter(category__slug=category)
        return qs

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        category = self.request.GET.get('category', None)
        if category:
            context.update({
                "category": Category.objects.get(slug=category)
            })
        return context

    context_object_name = 'products_list'
    paginate_by = 9


class ProductDetailView(generic.FormView):
    template_name = 'shop/product.html'
    form_class = AddToCartForm

    def get_object(self):
        return get_object_or_404(Product, slug=self.kwargs['slug'])

    def get_success_url(self):
        return reverse('cart')

    # method for passing the product_id to AddToCart form so that we get only the available colours for this product_id
    def get_form_kwargs(self):
        kwargs = super(ProductDetailView, self).get_form_kwargs()
        kwargs['product_id'] = self.get_object().id
        return kwargs

    def form_valid(self, form):
        order = get_or_set_order_session(self.request)
        product = self.get_object()
        colour = form.cleaned_data['colour']
        size = form.cleaned_data['size']

        # check if the product you choosed to add to the cart, already exists in the order's orderitem list
        item_filter = order.items.filter(
            product=product,
            colour=colour,
            size=size,
        )
        # if it exists
        if item_filter.exists():
            # it will be the first item in the list
            item = item_filter.first()
            # then increase this item's quantity
            item.quantity += int(form.cleaned_data['quantity'])
            item.save()
        # if it does not exist
        else:
            # create a new orderitem from the AddToCartForm which saves an orderitem instance
            new_item = form.save(commit=False)
            new_item.product = product
            new_item.order = order
            new_item.save()

        return super(ProductDetailView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(ProductDetailView, self).get_context_data(**kwargs)
        # context is a dictionary so we can add values
        context['product'] = self.get_object()
        return context
