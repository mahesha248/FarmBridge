from django.urls import path
from . import views

urlpatterns = [

    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    path(
        'admin-dashboard/',
        views.admin_dashboard,
        name='admin_dashboard'
    ),

    path(
        'admin-farmers/',
        views.admin_farmers,
        name='admin_farmers'
    ),

    path(
        'admin-customers/',
        views.admin_customers,
        name='admin_customers'
    ),

    path(
        'admin-products/',
        views.admin_products,
        name='admin_products'
    ),

    path(
        'admin-orders/',
        views.admin_orders,
        name='admin_orders'
    ),

    path(
        'admin-orders/<int:order_id>/',
        views.admin_order_details,
        name='admin_order_details'
    ),

    path(
        'farmer/dashboard/',
        views.farmer_dashboard,
        name='farmer_dashboard'
    ),

    path(
        'farmer/profile/',
        views.farmer_profile,
        name='farmer_profile'
    ),

    path(
        'farmer/sales/',
        views.farmer_sales,
        name='farmer_sales'
    ),

    path(
        'farmer/add-product/',
        views.add_product,
        name='add_product'
    ),

    path(
        'farmer/edit-product/<int:product_id>/',
        views.edit_product,
        name='edit_product'
    ),

    path(
        'farmer/delete-product/<int:product_id>/',
        views.delete_product,
        name='delete_product'
    ),

    path(
        'farmer/my-products/',
        views.my_products,
        name='my_products'
    ),

    path(
        'farmer/orders/',
        views.farmer_orders,
        name='farmer_orders'
    ),

    path(
        'farmer/orders/<int:order_id>/update-status/',
        views.update_order_status,
        name='update_order_status'
    ),

    path(
    'farmer/orders/<int:order_id>/mark-paid/',
    views.mark_payment_paid,
    name='mark_payment_paid'
    ),

    path(
        'customer/dashboard/',
        views.customer_dashboard,
        name='customer_dashboard'
    ),

    path(
        'customer/profile/',
        views.customer_profile,
        name='customer_profile'
    ),

    path(
        'customer/products/',
        views.customer_products,
        name='customer_products'
    ),

    path(
        'customer/add-to-cart/<int:product_id>/',
        views.add_to_cart,
        name='add_to_cart'
    ),

    path(
        'customer/cart/',
        views.cart,
        name='cart'
    ),

    path(
        'customer/increase-quantity/<int:item_id>/',
        views.increase_quantity,
        name='increase_quantity'
    ),

    path(
        'customer/decrease-quantity/<int:item_id>/',
        views.decrease_quantity,
        name='decrease_quantity'
    ),

    path(
        'customer/remove-from-cart/<int:item_id>/',
        views.remove_from_cart,
        name='remove_from_cart'
    ),

    path(
        'customer/checkout/',
        views.checkout,
        name='checkout'
    ),

    path(
        'customer/orders/',
        views.customer_orders,
        name='customer_orders'
    ),

    path(
        'customer/order/<int:order_id>/bill/',
        views.order_bill,
        name='order_bill'
    ),

    path(
        'customer/order/<int:order_id>/payment/',
        views.payment,
        name='payment'
    ),
]