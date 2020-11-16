from django import forms

from shop.models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'category', 'price', 'main_image', 'image1',
                  'image2', 'image3', 'stock', 'available_colours', 'available_sizes']
