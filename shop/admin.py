from django.contrib import admin
from .models import Product, Category, ColourVariation, SizeVariation, Customer


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


admin.site.register(Category, CategoryAdmin)


class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'stock',
                    'available', 'created', 'updated']
    list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 20
    filter_horizontal = ['available_colours', 'available_sizes']


admin.site.register(Product, ProductAdmin)

admin.site.register(ColourVariation)
admin.site.register(SizeVariation)
admin.site.register(Customer)
