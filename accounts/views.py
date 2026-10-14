from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.db import transaction
from functools import wraps


from .models import (
    UserProfile,
    Product,
    Cart,
    CartItem,
    Order,
    OrderItem,
    TabSession
)


# ===================================
# TAB SESSION / USER ROLE
# ===================================

def get_tab_token(request):

    tab_token = request.GET.get("tab_token")

    if not tab_token:
        tab_token = request.POST.get("tab_token")

    return tab_token


def get_tab_user(request):

    tab_token = get_tab_token(request)

    if not tab_token:
        return None

    try:

        tab_session = TabSession.objects.get(
            token=tab_token
        )

        return tab_session.user

    except TabSession.DoesNotExist:

        return None


def get_user_role(request):

    user = get_tab_user(request)

    if user is None:
        return None

    try:

        return user.userprofile.role

    except UserProfile.DoesNotExist:

        return None


# ===================================
# FARMER ACCESS
# ===================================

def farmer_required(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        user = get_tab_user(request)

        if user is None:

            return redirect(
                "/accounts/login/"
            )

        if get_user_role(request) != "farmer":

            tab_token = get_tab_token(request)

            return redirect(
                f"/accounts/customer/dashboard/?tab_token={tab_token}"
            )

        request.tab_user = user

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper


# ===================================
# CUSTOMER ACCESS
# ===================================

def customer_required(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        user = get_tab_user(request)

        if user is None:

            return redirect(
                "/accounts/login/"
            )

        if get_user_role(request) != "customer":

            tab_token = get_tab_token(request)

            return redirect(
                f"/accounts/farmer/dashboard/?tab_token={tab_token}"
            )

        request.tab_user = user

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper


# ===================================
# LOGIN
# ===================================

def login_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")
        tab_token = request.POST.get("tab_token")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None and tab_token:

            TabSession.objects.filter(
                token=tab_token
            ).delete()

            TabSession.objects.create(
                token=tab_token,
                user=user
            )

            if user.is_superuser:

                return redirect(
                    f"/accounts/admin-dashboard/?tab_token={tab_token}"
                )

            profile = UserProfile.objects.get(
                user=user
            )

            if profile.role == "farmer":

                return redirect(
                    f"/accounts/farmer/dashboard/?tab_token={tab_token}"
                )

            elif profile.role == "customer":

                return redirect(
                    f"/accounts/customer/dashboard/?tab_token={tab_token}"
                )

        else:

            messages.error(
                request,
                "Invalid username or password"
            )

    return render(
        request,
        "accounts/login.html"
    )


# ===================================
# REGISTER
# ===================================

def register_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        role = request.POST.get("role")

        if password != confirm_password:

            messages.error(
                request,
                "Passwords do not match"
            )

            return render(
                request,
                "accounts/register.html"
            )

        if User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                "Username already exists"
            )

            return render(
                request,
                "accounts/register.html"
            )

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        UserProfile.objects.create(
            user=user,
            role=role
        )

        send_mail(

            f"New {role.title()} Registered - FarmBridge",

            f"""
A new {role} has registered on FarmBridge.

Username: {username}
Email: {email}
Role: {role.title()}
""",

            None,

            ["mahiraj7022@gmail.com"],

            fail_silently=False,
        )

        messages.success(
            request,
            "Account created successfully. Please login."
        )

        return redirect(
            "/accounts/login/"
        )

    return render(
        request,
        "accounts/register.html"
    )


# ===================================
# FARMER SECTION
# ===================================

@farmer_required
def farmer_dashboard(request):

    total_products = Product.objects.filter(
        farmer=request.tab_user
    ).count()

    total_orders = OrderItem.objects.filter(
        product__farmer=request.tab_user
    ).values(
        "order"
    ).distinct().count()

    active_orders = OrderItem.objects.filter(
        product__farmer=request.tab_user
    ).exclude(
        status="delivered"
    ).count()

    delivered_items = OrderItem.objects.filter(
        product__farmer=request.tab_user,
        status="delivered"
    )

    total_sales = 0

    for item in delivered_items:
        total_sales += item.price * item.quantity

    return render(
        request,
        "accounts/farmer_dashboard.html",
        {
            "total_products": total_products,
            "total_orders": total_orders,
            "active_orders": active_orders,
            "total_sales": total_sales
        }
    )


# -----------------------------------
# ADD PRODUCT
# -----------------------------------

@farmer_required
def add_product(request):

    if request.method == "POST":

        from datetime import timedelta
        from django.utils import timezone

        name = request.POST.get("name")
        category = request.POST.get("category")
        image = request.POST.get("image")
        price = request.POST.get("price")
        quantity = request.POST.get("quantity")
        description = request.POST.get("description")
        freshness_days = request.POST.get("freshness_days")

        if not name or not category:

            return render(
                request,
                "accounts/add_product.html",
                {
                    "error": "Product name and category are required."
                }
            )

        if not image:

            return render(
                request,
                "accounts/add_product.html",
                {
                    "error": "Please select a product image."
                }
            )

        try:
            price_value = float(price)
        except (TypeError, ValueError):

            return render(
                request,
                "accounts/add_product.html",
                {
                    "error": "Price must be a valid number."
                }
            )

        if price_value <= 0:

            return render(
                request,
                "accounts/add_product.html",
                {
                    "error": "Price must be greater than 0."
                }
            )

        try:
            quantity_value = float(quantity)
        except (TypeError, ValueError):

            return render(
                request,
                "accounts/add_product.html",
                {
                    "error": "Quantity must be a valid number."
                }
            )

        if quantity_value <= 0:

            return render(
                request,
                "accounts/add_product.html",
                {
                    "error": "Quantity must be greater than 0."
                }
            )

        try:
            freshness_days_value = int(freshness_days)
        except (TypeError, ValueError):

            return render(
                request,
                "accounts/add_product.html",
                {
                    "error": "Please select a valid freshness duration."
                }
            )

        if freshness_days_value <= 0:

            return render(
                request,
                "accounts/add_product.html",
                {
                    "error": "Freshness duration must be greater than 0 days."
                }
            )

        product = Product.objects.create(

            farmer=request.tab_user,

            name=name,
            category=category,
            image=image,
            price=price,
            quantity=quantity,
            description=description,
            freshness_days=freshness_days_value
        )

        product.expiry_date = (
            product.added_at +
            timedelta(days=freshness_days_value)
        )

        product.is_expired = False

        product.save(
            update_fields=[
                "expiry_date",
                "is_expired"
            ]
        )

        return redirect(
            f"/accounts/farmer/dashboard/?tab_token={get_tab_token(request)}"
        )

    return render(
        request,
        "accounts/add_product.html"
    )


# -----------------------------------
# MY PRODUCTS
# -----------------------------------

@farmer_required
def my_products(request):

    from django.utils import timezone

    now = timezone.now()

    expired_products = Product.objects.filter(
        expiry_date__isnull=False,
        expiry_date__lte=now,
        is_expired=False
    )

    expired_products.update(
        is_expired=True
    )

    products = Product.objects.filter(
        farmer=request.tab_user,
        is_expired=False
    )

    return render(
        request,
        "accounts/my_products.html",
        {
            "products": products
        }
    )


# -----------------------------------
# EDIT PRODUCT
# -----------------------------------

@farmer_required
def edit_product(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id,
        farmer=request.tab_user
    )

    if request.method == "POST":

        name = request.POST.get("name")
        category = request.POST.get("category")
        image = request.POST.get("image")
        price = request.POST.get("price")
        quantity = request.POST.get("quantity")
        description = request.POST.get("description")

        if not name or not category:

            return render(
                request,
                "accounts/edit_product.html",
                {
                    "product": product,
                    "error": "Product name and category are required."
                }
            )

        try:
            price_value = float(price)
        except (TypeError, ValueError):

            return render(
                request,
                "accounts/edit_product.html",
                {
                    "product": product,
                    "error": "Price must be a valid number."
                }
            )

        if price_value <= 0:

            return render(
                request,
                "accounts/edit_product.html",
                {
                    "product": product,
                    "error": "Price must be greater than 0."
                }
            )

        try:
            quantity_value = float(quantity)
        except (TypeError, ValueError):

            return render(
                request,
                "accounts/edit_product.html",
                {
                    "product": product,
                    "error": "Quantity must be a valid number."
                }
            )

        if quantity_value <= 0:

            return render(
                request,
                "accounts/edit_product.html",
                {
                    "product": product,
                    "error": "Quantity must be greater than 0."
                }
            )

        product.name = name
        product.category = category
        product.image = image
        product.price = price
        product.quantity = quantity
        product.description = description

        product.save()

        return redirect(
            f"/accounts/farmer/my-products/?tab_token={request.GET.get('tab_token')}"
        )

    return render(
        request,
        "accounts/edit_product.html",
        {
            "product": product
        }
    )


# -----------------------------------
# DELETE PRODUCT
# -----------------------------------

@farmer_required
def delete_product(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id,
        farmer=request.tab_user
    )

    if request.method == "POST":

        product.delete()

        return redirect(
            f"/accounts/farmer/my-products/?tab_token={get_tab_token(request)}"
        )

    return redirect(
        f"/accounts/farmer/my-products/?tab_token={get_tab_token(request)}"
    )


# -----------------------------------
# FARMER ORDERS
# -----------------------------------

@farmer_required
def farmer_orders(request):

    orders = Order.objects.filter(
        items__product__farmer=request.tab_user
    ).distinct().order_by(
        "-created_at"
    )

    for order in orders:

        order.farmer_items = order.items.filter(
            product__farmer=request.tab_user
        )

    return render(
        request,
        "accounts/farmer_orders.html",
        {
            "orders": orders
        }
    )


# -----------------------------------
# MARK PAYMENT AS PAID
# -----------------------------------

@farmer_required
def mark_payment_paid(request, order_id):

    if request.method == "POST":

        order = get_object_or_404(
            Order,
            id=order_id
        )

        farmer_items = order.items.filter(
            product__farmer=request.tab_user
        )

        if farmer_items.exists():

            order.payment_status = "paid"

            order.save(
                update_fields=["payment_status"]
            )

    return redirect(
        f"/accounts/farmer/orders/?tab_token={get_tab_token(request)}"
    )


# -----------------------------------
# UPDATE ORDER STATUS
# -----------------------------------

@farmer_required
def update_order_status(request, order_id):

    if request.method == "POST":

        item_id = request.POST.get("item_id")
        status = request.POST.get("status")

        valid_statuses = [
            "placed",
            "confirmed",
            "preparing",
            "shipped",
            "delivered"
        ]

        if status in valid_statuses:

            # Update only the selected item
            order_item = get_object_or_404(
                OrderItem,
                id=item_id,
                order_id=order_id,
                product__farmer=request.tab_user
            )

            order_item.status = status
            order_item.save(update_fields=["status"])

            # Status priority
            status_priority = {
                "placed": 1,
                "confirmed": 2,
                "preparing": 3,
                "shipped": 4,
                "delivered": 5
            }

            # Get all items in this order
            all_items = OrderItem.objects.filter(
                order_id=order_id
            )

            if all_items.exists():

                # Find the least advanced item
                lowest_status = min(
                    all_items.values_list("status", flat=True),
                    key=lambda x: status_priority.get(x, 1)
                )

                # Update main order status
                order = get_object_or_404(
                    Order,
                    id=order_id
                )

                order.status = lowest_status
                order.save(update_fields=["status"])

    return redirect(
        f"/accounts/farmer/orders/?tab_token={get_tab_token(request)}"
    )


# -----------------------------------
# FARMER SALES
# -----------------------------------

@farmer_required
def farmer_sales(request):

    orders = Order.objects.filter(
        items__product__farmer=request.tab_user,
        items__status="delivered"
    ).distinct().order_by("-created_at")

    total_sales = 0

    for order in orders:

        farmer_items = order.items.filter(
            product__farmer=request.tab_user,
            status="delivered"
        )

        farmer_total = 0

        for item in farmer_items:
            farmer_total += item.price * item.quantity

        order.farmer_total = farmer_total
        total_sales += farmer_total

    return render(
        request,
        "accounts/farmer_sales.html",
        {
            "orders": orders,
            "total_sales": total_sales
        }
    )


# -----------------------------------
# FARMER PROFILE
# -----------------------------------

@farmer_required
def farmer_profile(request):

    user = request.tab_user
    profile = user.userprofile

    success = None
    error = None

    if request.method == "POST":

        first_name = request.POST.get(
            "first_name",
            ""
        ).strip()

        last_name = request.POST.get(
            "last_name",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip()

        phone = request.POST.get(
            "phone",
            ""
        ).strip()

        if not phone:

            error = "Phone number is required."

        else:

            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()

            profile.phone = phone
            profile.save()

            success = "Profile updated successfully."

    return render(
        request,
        "accounts/farmer_profile.html",
        {
            "user": user,
            "profile": profile,
            "success": success,
            "error": error,
        }
    )


# ===================================
# CUSTOMER DASHBOARD
# ===================================

@customer_required
def customer_dashboard(request):

    return render(
        request,
        "accounts/customer_dashboard.html"
    )


# -----------------------------------
# CUSTOMER PRODUCTS
# -----------------------------------

@customer_required
def customer_products(request):

    from django.utils import timezone

    now = timezone.now()

    expired_products = Product.objects.filter(
        expiry_date__isnull=False,
        expiry_date__lte=now,
        is_expired=False
    )

    expired_products.update(
        is_expired=True
    )

    products = Product.objects.filter(
        is_expired=False
    )

    return render(
        request,
        "accounts/customer_products.html",
        {
            "products": products
        }
    )


# -----------------------------------
# ADD TO CART
# -----------------------------------

@customer_required
def add_to_cart(request, product_id):

    if request.method == "POST":

        product = get_object_or_404(
            Product,
            id=product_id
        )

        if product.quantity <= 0:

            messages.error(
                request,
                f"{product.name} is currently out of stock."
            )

            return redirect(
                f"/accounts/customer/products/?tab_token={get_tab_token(request)}"
            )

        cart, created = Cart.objects.get_or_create(
            customer=request.tab_user
        )

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": 1}
        )

        if not created:

            if cart_item.quantity >= product.quantity:

                messages.error(
                    request,
                    f"Only {product.quantity} units of "
                    f"{product.name} are available."
                )

                return redirect(
                    f"/accounts/customer/products/?tab_token={get_tab_token(request)}"
                )

            cart_item.quantity += 1
            cart_item.save(update_fields=["quantity"])

        messages.success(
            request,
            f"{product.name} added to cart successfully!"
        )

    return redirect(
        f"/accounts/customer/products/?tab_token={get_tab_token(request)}"
    )


# -----------------------------------
# CART
# -----------------------------------

@customer_required
def cart(request):

    cart, created = Cart.objects.get_or_create(
        customer=request.tab_user
    )

    cart_items = CartItem.objects.filter(
        cart=cart
    )

    total = 0
    total_items = 0

    for item in cart_items:

        total_items += item.quantity

        total += (
            item.product.price *
            item.quantity
        )

    return render(
        request,
        "accounts/cart.html",
        {
            "cart_items": cart_items,
            "total": total,
            "total_items": total_items,
            "tab_token": get_tab_token(request)
        }
    )

# -----------------------------------
# INCREASE QUANTITY
# -----------------------------------

@customer_required
def increase_quantity(request, item_id):

    if request.method == "POST":

        cart_item = get_object_or_404(
            CartItem,
            id=item_id,
            cart__customer=request.tab_user
        )

        if cart_item.quantity >= cart_item.product.quantity:

            messages.error(
                request,
                f"Only {cart_item.product.quantity} units of "
                f"{cart_item.product.name} are available."
            )

        else:

            cart_item.quantity += 1
            cart_item.save(update_fields=["quantity"])

    return redirect(
        f"/accounts/customer/cart/?tab_token={get_tab_token(request)}"
    )


# -----------------------------------
# DECREASE QUANTITY
# -----------------------------------

@customer_required
def decrease_quantity(request, item_id):

    if request.method == "POST":

        cart_item = get_object_or_404(
            CartItem,
            id=item_id,
            cart__customer=request.tab_user
        )

        if cart_item.quantity > 1:

            cart_item.quantity -= 1
            cart_item.save(update_fields=["quantity"])

    return redirect(
        f"/accounts/customer/cart/?tab_token={get_tab_token(request)}"
    )


# -----------------------------------
# REMOVE FROM CART
# -----------------------------------

@customer_required
def remove_from_cart(request, item_id):

    if request.method == "POST":

        cart_item = get_object_or_404(
            CartItem,
            id=item_id,
            cart__customer=request.tab_user
        )

        cart_item.delete()

        messages.success(
            request,
            "Product removed from cart successfully."
        )

    return redirect(
        f"/accounts/customer/cart/?tab_token={get_tab_token(request)}"
    )


# -----------------------------------
# CHECKOUT
# -----------------------------------

@customer_required
def checkout(request):

    cart, created = Cart.objects.get_or_create(
        customer=request.tab_user
    )

    cart_items = CartItem.objects.filter(
        cart=cart
    ).select_related(
        "product",
        "product__farmer"
    )

    if not cart_items.exists():

        return render(
            request,
            "accounts/checkout.html",
            {
                "cart_items": [],
                "total": 0,
                "error": "Your cart is empty."
            }
        )

    total = 0

    for item in cart_items:

        # CartItem.item_total is a @property.
        # So we calculate it without assigning a value to it.
        total += item.product.price * item.quantity

    if request.method == "POST":

        address = request.POST.get(
            "address",
            ""
        ).strip()

        phone = request.POST.get(
            "phone",
            ""
        ).strip()

        payment_method = request.POST.get(
            "payment_method",
            ""
        ).strip()

        if not address:

            return render(
                request,
                "accounts/checkout.html",
                {
                    "cart_items": cart_items,
                    "total": total,
                    "address": address,
                    "phone": phone,
                    "error": "Delivery address is required."
                }
            )

        if not phone.isdigit() or len(phone) != 10:

            return render(
                request,
                "accounts/checkout.html",
                {
                    "cart_items": cart_items,
                    "total": total,
                    "address": address,
                    "phone": phone,
                    "error": "Please enter a valid 10-digit phone number."
                }
            )

        if payment_method not in [
            "Cash on Delivery",
            "Pay Directly to Farmer"
        ]:

            return render(
                request,
                "accounts/checkout.html",
                {
                    "cart_items": cart_items,
                    "total": total,
                    "address": address,
                    "phone": phone,
                    "error": "Please select a valid payment method."
                }
            )

        # -----------------------------------
        # CHECK STOCK AND CREATE ORDER
        # -----------------------------------

        with transaction.atomic():

            # Check every product's current stock
            for item in cart_items:

                product = Product.objects.select_for_update().get(
                    id=item.product.id
                )

                if item.quantity > product.quantity:

                    error_message = (
                        f"Only {product.quantity} units of "
                        f"{product.name} are available."
                    )

                    return render(
                        request,
                        "accounts/checkout.html",
                        {
                            "cart_items": cart_items,
                            "total": total,
                            "address": address,
                            "phone": phone,
                            "error": error_message
                        }
                    )

            # Create order
            order = Order.objects.create(
                customer=request.tab_user,
                address=address,
                phone=phone,
                total_amount=total,
                payment_method=payment_method,
                payment_status="pending"
            )

            # Create order items and reduce stock
            for item in cart_items:

                product = Product.objects.select_for_update().get(
                    id=item.product.id
                )

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item.quantity,
                    price=product.price
                )

                # Reduce product stock
                product.quantity -= item.quantity
                product.save(update_fields=["quantity"])

        # -----------------------------------
        # SEND ADMIN EMAIL
        # -----------------------------------

        admin_message = f"""
New FarmBridge Order

Order ID:
{order.id}

Customer:
{request.tab_user.username}

Phone:
{phone}

Delivery Address:
{address}

Payment Method:
{payment_method}

Total Amount:
₹{total}

Products:
"""

        for item in cart_items:

            admin_message += (
                f"\n{item.product.name} - "
                f"Quantity: {item.quantity} - "
                f"₹{item.item_total}"
            )

        send_mail(
            f"New FarmBridge Order #{order.id}",
            admin_message,
            None,
            ["mahiraj7022@gmail.com"],
            fail_silently=True
        )

        # -----------------------------------
        # SEND FARMER EMAILS
        # -----------------------------------

        farmers = {}

        for item in cart_items:

            farmer = item.product.farmer

            if farmer.email:

                if farmer not in farmers:
                    farmers[farmer] = []

                farmers[farmer].append(item)

        for farmer, items in farmers.items():

            farmer_message = f"""
New FarmBridge Order

Order ID:
{order.id}

Customer:
{request.tab_user.username}

Customer Phone:
{phone}

Delivery Address:
{address}

Payment Method:
{payment_method}

Products:
"""

            farmer_total = 0

            for item in items:

                item_total = (
                    item.product.price *
                    item.quantity
                )

                farmer_total += item_total

                farmer_message += (
                    f"\n{item.product.name} - "
                    f"Quantity: {item.quantity} - "
                    f"₹{item_total}"
                )

            farmer_message += (
                f"\n\nFarmer Order Total: ₹{farmer_total}"
            )

            send_mail(
                f"New FarmBridge Order #{order.id}",
                farmer_message,
                None,
                [farmer.email],
                fail_silently=True
            )

        # -----------------------------------
        # CLEAR CART
        # -----------------------------------

        cart_items.delete()

        return redirect(
            f"/accounts/customer/order/{order.id}/payment/"
            f"?tab_token={get_tab_token(request)}"
        )

    return render(
        request,
        "accounts/checkout.html",
        {
            "cart_items": cart_items,
            "total": total
        }
    )


# -----------------------------------
# CUSTOMER ORDERS
# -----------------------------------

@customer_required
def customer_orders(request):

    orders = Order.objects.filter(
        customer=request.tab_user
    ).prefetch_related(
        "items__product"
    ).order_by(
        "-created_at"
    )

    return render(
        request,
        "accounts/customer_orders.html",
        {
            "orders": orders
        }
    )


# -----------------------------------
# ORDER BILL
# -----------------------------------

@customer_required
def order_bill(request, order_id):

    order = Order.objects.get(
        id=order_id,
        customer=request.tab_user
    )

    return render(
        request,
        "accounts/order_bill.html",
        {
            "order": order
        }
    )


# -----------------------------------
# PAYMENT
# -----------------------------------

@customer_required
def payment(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        customer=request.tab_user
    )

    farmer_contacts = []

    farmers = User.objects.filter(
        product__orderitem__order=order
    ).distinct()

    for farmer in farmers:

        profile = getattr(
            farmer,
            "userprofile",
            None
        )

        phone = ""

        if profile:
            phone = profile.phone

        farmer_contacts.append({
            "farmer": farmer,
            "phone": phone
        })

    if request.method == "POST":

        payment_method = request.POST.get(
            "payment_method"
        )

        valid_payment_methods = [
            "Cash on Delivery",
            "Pay Directly to Farmer"
        ]

        if payment_method not in valid_payment_methods:

            messages.error(
                request,
                "Please select a valid payment method."
            )

            return redirect(
                f"/accounts/customer/order/{order.id}/payment/?tab_token={get_tab_token(request)}"
            )

        order.payment_method = payment_method
        order.payment_status = "pending"

        order.save(
            update_fields=[
                "payment_method",
                "payment_status"
            ]
        )

        return redirect(
            f"/accounts/customer/orders/?tab_token={get_tab_token(request)}"
        )

    return render(
        request,
        "accounts/payment.html",
        {
            "order": order,
            "farmer_contacts": farmer_contacts,
            "tab_token": get_tab_token(request)
        }
    )


# -----------------------------------
# CUSTOMER PROFILE
# -----------------------------------

@customer_required
def customer_profile(request):

    user = request.tab_user

    if request.method == "POST":

        user.first_name = request.POST.get(
            "first_name",
            ""
        ).strip()

        user.last_name = request.POST.get(
            "last_name",
            ""
        ).strip()

        user.email = request.POST.get(
            "email",
            ""
        ).strip()

        user.save()

        messages.success(
            request,
            "Profile updated successfully!"
        )

        return redirect(
            f"/accounts/customer/profile/?tab_token={get_tab_token(request)}"
        )

    return render(
        request,
        "accounts/customer_profile.html",
        {
            "user": user
        }
    )


# ===================================
# ADMIN DASHBOARD
# ===================================

def admin_dashboard(request):

    user = get_tab_user(request)

    if user is None or not user.is_superuser:

        return redirect(
            "/accounts/login/"
        )

    total_farmers = UserProfile.objects.filter(
        role="farmer"
    ).count()

    total_customers = UserProfile.objects.filter(
        role="customer"
    ).count()

    total_products = Product.objects.count()

    total_orders = Order.objects.count()

    delivered_items = OrderItem.objects.filter(
        status="delivered"
    )

    total_sales = 0

    for item in delivered_items:

        total_sales += item.price * item.quantity

    pending_orders = Order.objects.exclude(
        status="delivered"
    ).count()

    paid_orders = Order.objects.filter(
        payment_status="paid"
    ).count()

    return render(
        request,
        "accounts/admin_dashboard.html",
        {
            "total_farmers": total_farmers,
            "total_customers": total_customers,
            "total_products": total_products,
            "total_orders": total_orders,
            "total_sales": total_sales,
            "pending_orders": pending_orders,
            "paid_orders": paid_orders
        }
    )


def admin_farmers(request):

    user = get_tab_user(request)

    if user is None or not user.is_superuser:

        return redirect(
            "/accounts/login/"
        )

    farmers = User.objects.filter(
        userprofile__role="farmer"
    ).order_by("username")

    return render(
        request,
        "accounts/admin_farmers.html",
        {
            "farmers": farmers
        }
    )


def admin_customers(request):

    user = get_tab_user(request)

    if user is None or not user.is_superuser:

        return redirect(
            "/accounts/login/"
        )

    customers = User.objects.filter(
        userprofile__role="customer"
    ).order_by("username")

    return render(
        request,
        "accounts/admin_customers.html",
        {
            "customers": customers
        }
    )


def admin_products(request):

    user = get_tab_user(request)

    if user is None or not user.is_superuser:

        return redirect(
            "/accounts/login/"
        )

    products = Product.objects.select_related(
        "farmer"
    ).order_by("name")

    return render(
        request,
        "accounts/admin_products.html",
        {
            "products": products
        }
    )


def admin_orders(request):

    user = get_tab_user(request)

    if user is None or not user.is_superuser:

        return redirect(
            "/accounts/login/"
        )

    orders = Order.objects.select_related(
        "customer"
    ).prefetch_related(
        "items__product__farmer"
    ).order_by("-id")

    return render(
        request,
        "accounts/admin_orders.html",
        {
            "orders": orders
        }
    )


def admin_order_details(request, order_id):

    user = get_tab_user(request)

    if user is None or not user.is_superuser:

        return redirect(
            "/accounts/login/"
        )

    order = get_object_or_404(
        Order.objects.select_related(
            "customer"
        ).prefetch_related(
            "items__product__farmer"
        ),
        id=order_id
    )

    return render(
        request,
        "accounts/admin_order_details.html",
        {
            "order": order
        }
    )


# ===================================
# LOGOUT
# ===================================

def logout_view(request):

    tab_token = get_tab_token(request)

    if tab_token:

        TabSession.objects.filter(
            token=tab_token
        ).delete()

    return redirect(
        "/accounts/login/"
    )