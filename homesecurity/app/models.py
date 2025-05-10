from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator

# Choices for Product category
CATEGORY_CHOICES = [
    ('Lighting', 'Lighting'),
    ('Actuators', 'Actuators'),
    ('Touch Switches', 'Touch Switches'),
    ('Security', 'Security'),
]

# Choices for Order status
STATUS_CHOICES = [
    ('Pending', 'Pending'),
    ('Placed', 'Placed'),
    ('Confirmed', 'Confirmed'),
    ('Shipped', 'Shipped'),
    ('Delivered', 'Delivered'),
    ('Cancelled', 'Cancelled'),
]

# Choices for Payment method
PAYMENT_METHOD_CHOICES = [
    ('COD', 'Cash on Delivery'),
    ('Online', 'Online Payment'),
]

# Function to provide default delivery date (7 days from now)
def default_delivery_date():
    return timezone.localdate() + timezone.timedelta(days=7)

class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    offer_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    description = models.TextField()
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    warranty = models.CharField(max_length=100, blank=True, null=True)
    stock = models.PositiveIntegerField(default=1)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=['category']),
        ]

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

    def clear(self):
        self.items.all().delete()

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    def __str__(self):
        return f"{self.quantity} of {self.product.name}"

    def get_total_price(self):
        price = self.product.offer_price or self.product.price
        return price * self.quantity

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    address = models.TextField()
    pincode = models.CharField(max_length=6)  # Standardized for 6-digit PIN (e.g., India)
    phone = models.CharField(max_length=15)  # Standardized length
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.address[:30]}"

    def save(self, *args, **kwargs):
        # Ensure only one default address per user
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(is_default=True),
                name='unique_default_address_per_user'
            )
        ]

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.PROTECT)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateField(default=default_delivery_date)  # Use callable function
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"

    class Meta:
        indexes = [
            models.Index(fields=['user', 'status']),
        ]

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of order

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def save(self, *args, **kwargs):
        # Set price at the time of order creation and validate stock
        if not self.pk:  # Only set price and check stock when creating
            if self.quantity > self.product.stock:
                raise ValueError(f"Insufficient stock for {self.product.name}")
            self.price = self.product.offer_price or self.product.price
            self.product.stock -= self.quantity
            self.product.save()
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['order', 'product']),
        ]