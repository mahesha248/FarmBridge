from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):

    ROLE_CHOICES = (
        ('farmer', 'Farmer'),
        ('customer', 'Customer'),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    phone = models.CharField(
        max_length=15,
        blank=True
    )

    def __str__(self):
        return self.user.username


class Product(models.Model):

    farmer = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    name = models.CharField(
        max_length=100
    )

    category = models.CharField(
        max_length=100
    )

    image = models.CharField(
        max_length=100,
        blank=True
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    description = models.TextField(
        blank=True
    )

    freshness_days = models.PositiveIntegerField(
        default=3
    )

    added_at = models.DateTimeField(
        default=timezone.now
    )

    expiry_date = models.DateTimeField(
        null=True,
        blank=True
    )

    is_expired = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.name


class Cart(models.Model):

    customer = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.customer.username


class CartItem(models.Model):

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"],
                name="unique_cart_product"
            )
        ]

    @property
    def item_total(self):
        return self.product.price * self.quantity

    def __str__(self):
        return self.product.name

class Order(models.Model):

    STATUS_CHOICES = (
        ('placed', 'Placed'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    )

    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    address = models.TextField()

    phone = models.CharField(
        max_length=15
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='placed'
    )

    payment_method = models.CharField(
        max_length=20,
        blank=True
    )

    payment_status = models.CharField(
        max_length=20,
        default='pending'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Order {self.id} - {self.customer.username}"


class OrderItem(models.Model):

    STATUS_CHOICES = (
        ('placed', 'Placed'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='placed'
    )

    @property
    def item_total(self):
        return self.price * self.quantity

    def __str__(self):
        return self.product.name


class TabSession(models.Model):

    token = models.CharField(
        max_length=100,
        unique=True
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.token}"