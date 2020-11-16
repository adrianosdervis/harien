from django.db import models
from django.urls import reverse
from django.db.models.signals import pre_save, post_save
from django.utils.text import slugify
from django.contrib.auth import get_user_model

User = get_user_model()


class ColourVariation(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class SizeVariation(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to='category_images', default='placeholder.png')

    class Meta:
        ordering = ('name',)
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category, related_name='products', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    main_image = models.ImageField(
        upload_to='product_images', default='placeholder.png')
    image1 = models.ImageField(
        upload_to='product_images', blank=True)
    image2 = models.ImageField(
        upload_to='product_images', blank=True)
    image3 = models.ImageField(
        upload_to='product_images', blank=True)
    stock = models.PositiveSmallIntegerField()
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    available_colours = models.ManyToManyField(ColourVariation)
    available_sizes = models.ManyToManyField(SizeVariation)

    class Meta:
        ordering = ('name',)

    def get_url(self):
        return reverse('product', kwargs={'slug': self.slug})

    def get_update_url(self):
        return reverse('product-update', kwargs={'pk': self.pk})

    def get_delete_url(self):
        return reverse('product-delete', kwargs={'pk': self.pk})

    def __str__(self):
        return self.name


def pre_save_product_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = slugify(instance.name)


pre_save.connect(pre_save_product_receiver, sender=Product)


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=100)

    def __str__(self):
        return self.user.email


def post_save_user_receiver(sender, instance, created, **kwargs):
    if created:
        Customer.objects.create(user=instance)


post_save.connect(post_save_user_receiver, sender=User)
