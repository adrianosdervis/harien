from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.shortcuts import reverse
from cart.models import Order
from shop.models import Product
from .mixins import StaffUserMixin
from .forms import ProductForm


class StaffView(LoginRequiredMixin, StaffUserMixin, generic.ListView):
    template_name = 'staff/staff.html'
    queryset = Order.objects.filter(ordered=True).order_by('-ordered_date')
    paginate_by = 10
    context_object_name = 'orders'


class StaffOrderDetailView(LoginRequiredMixin, StaffUserMixin, generic.DetailView):
    template_name = 'staff/order-detail.html'
    queryset = Order.objects.all()
    context_object_name = 'order'


class ProductListView(LoginRequiredMixin, StaffUserMixin, generic.ListView):
    template_name = 'staff/product-list.html'
    queryset = Product.objects.all()
    paginate_by = 10
    context_object_name = 'products'


class ProductCreateView(LoginRequiredMixin, StaffUserMixin, generic.CreateView):
    template_name = 'staff/product-create.html'
    form_class = ProductForm

    def get_success_url(self):
        return reverse('product-list')

    def form_valid(self, form):
        form.save()
        return super(ProductCreateView, self).form_valid(form)


class ProductUpdateView(LoginRequiredMixin, StaffUserMixin, generic.UpdateView):
    template_name = 'staff/product-update.html'
    form_class = ProductForm
    queryset = Product.objects.all()

    def get_success_url(self):
        return reverse('product-list')

    def form_valid(self, form):
        form.save()
        return super(ProductUpdateView, self).form_valid(form)


class ProductDeleteView(LoginRequiredMixin, StaffUserMixin, generic.DeleteView):
    template_name = 'staff/product-delete.html'
    queryset = Product.objects.all()
    context_object_name = 'product'

    def get_success_url(self):
        return reverse('product-list')
