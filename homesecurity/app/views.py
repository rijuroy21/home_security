from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import random
from .models import Product, Cart, CartItem, Order, OrderItem, Address
import razorpay

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def index(request):
    products = Product.objects.all().order_by('-id')[:10]
    return render(request, "index.html", {"products": products})

def product(request, id):
    product = get_object_or_404(Product, id=id)
    cart_item_ids = []

    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart_item_ids = cart.items.values_list('product_id', flat=True)

    additional_images = [product.image] if product.image else []
    similar_products = Product.objects.filter(category=product.category).exclude(id=product.id)

    return render(request, 'product.html', {
        'product': product,
        'cart_item_ids': cart_item_ids,
        'additional_images': additional_images,
        'similar_products': similar_products,
    })

def product_list(request):
    products = Product.objects.all()
    categories = Product.objects.values_list('category', flat=True).distinct()

    category = request.GET.get('category')
    sort = request.GET.get('sort')

    if category:
        products = products.filter(category=category)
    
    if sort == 'newest':
        products = products.order_by('-id')
    elif sort == 'low_to_high':
        products = products.order_by('offer_price')
    elif sort == 'high_to_low':
        products = products.order_by('-offer_price')

    return render(request, 'allproduct.html', {
        'products': products,
        'categories': categories,
    })

def search_results(request):
    query = request.GET.get('q')
    results = Product.objects.filter(name__icontains=query) if query else Product.objects.all()
    return render(request, 'search.html', {'results': results, 'query': query})

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confpassword = request.POST['confpassword']

        if password != confpassword:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already in use.")
            return redirect('register')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        messages.success(request, "Registration successful. Please login.")
        return redirect('login')

    return render(request, 'register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('firstpage')
            else:
                return redirect('index')
        else:
            messages.error(request, "Invalid credentials")
            return redirect('login')

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        otp = random.randint(100000, 999999)

        request.session['reset_email'] = email
        request.session['otp'] = otp

        send_mail(
            subject='Your OTP Code',
            message=f'Your OTP is {otp}',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )

        messages.success(request, 'OTP has been sent to your email.')
        return redirect('verify_otp')

    return render(request, 'forgot_password.html')

def verify_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        if str(request.session.get('otp')) == entered_otp:
            messages.success(request, 'OTP verified. You can now reset your password.')
            return redirect('reset_password')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')

    return render(request, 'verify_otp.html')

def reset_password(request):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        email = request.session.get('reset_email')

        user = User.objects.filter(email=email).first()
        if user:
            user.set_password(new_password)
            user.save()
            messages.success(request, "Password has been reset. You can now log in.")
            return redirect('login')
        else:
            messages.error(request, "Something went wrong. Please try again.")
            return redirect('forgot_password')

    return render(request, 'reset_password.html')

def first_page(request):
    products = Product.objects.all()
    return render(request, 'firstpage.html', {'products': products})

def delete_g(request, id):
    get_object_or_404(Product, pk=id).delete()
    return redirect('firstpage')

def edit_g(request, id):
    product = get_object_or_404(Product, id=id)

    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.price = request.POST.get('price')
        product.offer_price = request.POST.get('offer_price') or None
        product.category = request.POST.get('category')
        product.warranty = request.POST.get('warranty')
        product.description = request.POST.get('description')
        product.stock = request.POST.get('stock')

        if 'image' in request.FILES:
            product.image = request.FILES['image']

        product.save()
        messages.success(request, 'Product updated successfully!')
        return redirect('firstpage')

    return render(request, 'add.html', {'data1': product})

def add_product(request):
    if request.method == 'POST':
        stock = request.POST.get('stock')

        if not stock:
            messages.error(request, "Stock is required.")
            return redirect('add_product')

        if int(stock) < 0:
            messages.error(request, "Invalid stock value.")
            return redirect('add_product')

        Product.objects.create(
            name=request.POST.get('name'),
            price=request.POST.get('price'),
            offer_price=request.POST.get('offer_price') or None,
            description=request.POST.get('description'),
            category=request.POST.get('category'),
            warranty=request.POST.get('warranty'),
            stock=stock,
            image=request.FILES.get('image'),
        )
        messages.success(request, "Product added successfully!")
        return redirect('firstpage')

    return render(request, 'add.html')

@login_required(login_url='login')
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if product.stock <= 0:
        messages.error(request, "Product is out of stock.")
        return redirect('product', id=product_id)

    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not created and cart_item.quantity >= product.stock:
        messages.error(request, "Stock limit reached.")
        return redirect('cart_view')

    cart_item.quantity += 1
    cart_item.save()
    messages.success(request, "Item added to cart.")
    return redirect('cart_view')

@login_required(login_url='login')
def increment_cart(request, id):
    cart_item = get_object_or_404(CartItem, id=id, cart__user=request.user)
    product = cart_item.product

    if product.stock <= 0:
        messages.error(request, "No more stock available.")
        return redirect('cart_view')

    cart_item.quantity += 1
    cart_item.save()
    messages.success(request, "Quantity updated.")
    return redirect('cart_view')

@login_required(login_url='login')
def decrement_cart(request, id):
    cart_item = get_object_or_404(CartItem, id=id, cart__user=request.user)

    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
        messages.success(request, "Quantity updated.")
    else:
        cart_item.delete()
        messages.success(request, "Item removed from cart.")

    return redirect('cart_view')

@login_required(login_url='login')
def buy_now(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if product.stock <= 0:
        messages.error(request, "Product is out of stock.")
        return redirect('product', id=product_id)

    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart.clear()  # Clear existing cart items
    CartItem.objects.create(cart=cart, product=product, quantity=1)
    return redirect('checkout')

@login_required(login_url='login')
def delete_cart_item(request, id):
    cart_item = get_object_or_404(CartItem, id=id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, "Item removed from cart.")
    return redirect('cart_view')

@login_required(login_url='login')
def cart_view(request):
    cart = Cart.objects.filter(user=request.user).first()
    cart_items = cart.items.all() if cart else []
    total_price = cart.get_total_price() if cart else 0
    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price})

@login_required(login_url='login')
def checkout(request):
    cart = Cart.objects.filter(user=request.user).first()
    if not cart or not cart.items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('cart_view')

    addresses = Address.objects.filter(user=request.user)
    cart_items = cart.items.all()
    total_price = cart.get_total_price()

    razorpay_order = None
    if total_price > 0:
        razorpay_order = client.order.create({
            "amount": int(total_price * 100),  # Convert to paise
            "currency": "INR",
            "payment_capture": "1"
        })

    context = {
        'cart_items': cart_items,
        'items_total': cart_items.count(),
        'total_price': total_price,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'razorpay_amount': total_price,
        'razorpay_order_id': razorpay_order['id'] if razorpay_order else '',
        'addresses': addresses,
    }
    return render(request, 'checkout.html', context)

@csrf_exempt
def process_checkout(request):
    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        payment_method = request.POST.get('payment_method')
        razorpay_payment_id = request.POST.get('razorpay_payment_id', '')

        cart = Cart.objects.filter(user=request.user).first()
        if not cart or not cart.items.exists():
            messages.error(request, "Your cart is empty.")
            return redirect('cart_view')

        address = get_object_or_404(Address, id=address_id, user=request.user)
        total_price = cart.get_total_price()

        # Create the order
        order = Order.objects.create(
            user=request.user,
            address=address,
            payment_method=payment_method,
            total_price=total_price,
            razorpay_payment_id=razorpay_payment_id,
            status='Confirmed' if payment_method == 'Online' else 'Pending',
        )

        # Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.offer_price or cart_item.product.price
            )

        # Clear the cart
        cart.clear()
        messages.success(request, "Order placed successfully!")
        return redirect('order_success')

    return redirect('checkout')

def payment_successful(request):
    return render(request, 'payment_successful.html')

def order_success(request):
    return render(request, 'order_success.html')

@login_required(login_url='login')
def order_tracking(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product')
    return render(request, 'order_tracking.html', {'orders': orders})

@login_required(login_url='login')
def track_order(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        try:
            order = Order.objects.prefetch_related('items__product').get(id=order_id, user=request.user)
            return render(request, 'order_tracking.html', {
                'order': order,
                'order_items': order.items.all(),
                'order_status': order.status,
            })
        except Order.DoesNotExist:
            messages.error(request, 'Order not found.')
            return render(request, 'order_tracking.html', {'error': 'Order not found'})

    return redirect('order_tracking')

@login_required(login_url='login')
def user_list(request):
    if not request.user.is_superuser:
        return render(request, 'unauthorized.html')
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'user_list.html', {'users': users})

@login_required(login_url='login')
def user_detail(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    addresses = Address.objects.filter(user=user_obj)
    orders = Order.objects.filter(user=user_obj).prefetch_related('items__product')

    context = {
        'user_obj': user_obj,
        'addresses': addresses,
        'orders': orders,
    }
    return render(request, 'user_detail.html', context)

@login_required(login_url='login')
def delete_user(request, user_id):
    if not request.user.is_superuser:
        return render(request, 'unauthorized.html')
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, "User deleted successfully.")
    return redirect('user_list')

@login_required(login_url='login')
def profile_view(request):
    addresses = Address.objects.filter(user=request.user)
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product')

    editing_address = False
    address_to_edit = None
    name = phone = pincode = address = ''
    errors = {}

    address_id = request.GET.get('edit')
    if address_id:
        try:
            address_to_edit = Address.objects.get(id=address_id, user=request.user)
            editing_address = True
            name = address_to_edit.name
            phone = address_to_edit.phone
            pincode = address_to_edit.pincode
            address = address_to_edit.address
        except Address.DoesNotExist:
            pass

    context = {
        'addresses': addresses,
        'orders': orders,
        'editing_address': editing_address,
        'address_to_edit': address_to_edit,
        'name': name,
        'phone': phone,
        'pincode': pincode,
        'address': address,
        'errors': errors,
        'action': 'Edit' if editing_address else 'Add',
    }
    return render(request, 'profile.html', context)

@login_required(login_url='login')
def add_address(request):
    if request.method == 'POST':
        name = request.POST.get('name', '')
        address = request.POST.get('address', '')
        pincode = request.POST.get('pincode', '')
        phone = request.POST.get('phone', '')

        errors = {}
        if not name:
            errors['name'] = 'Name is required.'
        if not address:
            errors['address'] = 'Address is required.'
        if not pincode:
            errors['pincode'] = 'Pincode is required.'
        if not phone:
            errors['phone'] = 'Phone number is required.'

        if not errors:
            Address.objects.create(
                user=request.user,
                name=name,
                address=address,
                pincode=pincode,
                phone=phone
            )
            messages.success(request, 'Address added successfully!')
            return redirect('profile')
        else:
            return render(request, 'address_form.html', {
                'errors': errors,
                'name': name,
                'address': address,
                'pincode': pincode,
                'phone': phone,
                'action': 'Add'
            })

    return render(request, 'address_form.html', {
        'action': 'Add',
        'name': '',
        'address': '',
        'pincode': '',
        'phone': '',
        'errors': {}
    })

@login_required(login_url='login')
def edit_address(request, address_id):
    address_obj = get_object_or_404(Address, id=address_id, user=request.user)

    if request.method == 'POST':
        name = request.POST.get('name', '')
        address = request.POST.get('address', '')
        pincode = request.POST.get('pincode', '')
        phone = request.POST.get('phone', '')

        errors = {}
        if not name:
            errors['name'] = 'Name is required.'
        if not address:
            errors['address'] = 'Address is required.'
        if not pincode:
            errors['pincode'] = 'Pincode is required.'
        if not phone:
            errors['phone'] = 'Phone number is required.'

        if not errors:
            address_obj.name = name
            address_obj.address = address
            address_obj.pincode = pincode
            address_obj.phone = phone
            address_obj.save()
            messages.success(request, 'Address updated successfully!')
            return redirect('profile')
        else:
            return render(request, 'address_form.html', {
                'errors': errors,
                'name': name,
                'address': address,
                'pincode': pincode,
                'phone': phone,
                'action': 'Edit'
            })

    return render(request, 'address_form.html', {
        'name': address_obj.name,
        'address': address_obj.address,
        'pincode': address_obj.pincode,
        'phone': address_obj.phone,
        'action': 'Edit',
        'errors': {}
    })

@login_required(login_url='login')
def delete_address(request, address_id):
    address_obj = get_object_or_404(Address, id=address_id, user=request.user)
    address_obj.delete()
    messages.success(request, 'Address deleted successfully!')
    return redirect('profile')

@login_required(login_url='login')
def edit_email(request):
    user = request.user
    if request.method == 'POST':
        email = request.POST.get('email', '')
        errors = {}
        if not email:
            errors['email'] = 'Email is required.'
        elif '@' not in email:
            errors['email'] = 'Please enter a valid email address.'
        elif User.objects.filter(email=email).exclude(id=user.id).exists():
            errors['email'] = 'This email is already in use.'

        if not errors:
            user.email = email
            user.save()
            messages.success(request, 'Email updated successfully!')
            return redirect('profile')
        else:
            return render(request, 'email.html', {
                'errors': errors,
                'email': email
            })

    return render(request, 'email.html', {'email': user.email})

@login_required(login_url='login')
def edit_username(request):
    user = request.user
    if request.method == 'POST':
        username = request.POST.get('username', '')
        errors = {}
        if not username:
            errors['username'] = 'Username is required.'
        elif len(username) < 4:
            errors['username'] = 'Username should be at least 4 characters long.'
        elif User.objects.filter(username=username).exclude(id=user.id).exists():
            errors['username'] = 'This username is already taken.'

        if not errors:
            user.username = username
            user.save()
            messages.success(request, 'Username updated successfully!')
            return redirect('profile')
        else:
            return render(request, 'username.html', {
                'errors': errors,
                'username': username
            })

    return render(request, 'username.html', {'username': user.username})

def category(request):
    categories = Product.objects.values_list('category', flat=True).distinct()
    return render(request, 'category.html', {'categories': categories})

def terms(request):
    return render(request, 'terms.html')

def privacy(request):
    return render(request, 'privacy.html')

def contact(request):
    return render(request, 'contact.html')