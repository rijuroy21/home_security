from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('', views.index, name='index'),
    path('category/', views.category, name='category'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('contact/', views.contact, name='contact'),
    path('product/<int:id>/', views.product, name='product'),
    path('products/', views.product_list, name='product_list'),
    path('search/', views.search_results, name='search_results'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/increment/<int:id>/', views.increment_cart, name='increment_cart'),
    path('cart/decrement/<int:id>/', views.decrement_cart, name='decrement_cart'),
    path('cart/delete/<int:id>/', views.delete_cart_item, name='delete_cart_item'),
    path('checkout/', views.checkout, name='checkout'),
    path('process-checkout/', views.process_checkout, name='process_checkout'),
    path('buy-now/<int:product_id>/', views.buy_now, name='buy_now'),
    path('order-success/', views.order_success, name='order_success'),
    path('dashboard/', views.first_page, name='firstpage'),
    path('dashboard/add-product/', views.add_product, name='add_product'),
    path('dashboard/edit/<int:id>/', views.edit_g, name='edit_g'),
    path('dashboard/delete/<int:id>/', views.delete_g, name='delete_g'),
    path('payment-successful/', views.payment_successful, name='payment_successful'),
    path('order-tracking/', views.order_tracking, name='order_tracking'),
    path('track-order/', views.track_order, name='track_order'),
    path('user-list/', views.user_list, name='user_list'),
    path('user/<int:user_id>/', views.user_detail, name='user_detail'),
    path('user/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('profile/edit-email/', views.edit_email, name='edit_email'),
    path('profile/edit-username/', views.edit_username, name='edit_username'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/add-address/', views.add_address, name='add_address'),
    path('profile/edit-address/<int:address_id>/', views.edit_address, name='edit_address'),
    path('profile/delete-address/<int:address_id>/', views.delete_address, name='delete_address'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)