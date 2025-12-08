from django.urls import path, register_converter
from . import views
from .converter import FloatConverter
from django.contrib import admin

admin.site.site_header = "Mfamle administration"
admin.site.site_title = "Mfamle Admin Portal"
admin.site.index_title = "Welcome to Mfamle Admin"

# Register the custom converter
register_converter(FloatConverter, 'float')

urlpatterns = [
    path('',views.index,name='index'),
    path('index',views.index,name='index'),
    path('about/',views.about,name='about'),
    path('contact/',views.contact,name='contact'),
    path('services/',views.services,name='services'),
    path('login/',views.login,name='login'),
    path('shop/',views.shop,name='shop'),
    path('create_account/',views.create_account,name='create_account'),
    path('login_user/',views.login_user,name='login_user'),
    path('logout/',views.logout,name='logout'),
    path('register/',views.register,name='register'),
    path('mpesa_checkout',views.mpesa_checkout,name='mpesa_checkout'),
    path('card_checkout',views.CardPayments,name="card_checkout"),
    path('paymentProcessing',views.PaymentCallback,name='paymentProcessing'),
    path('payment/<float:amount>', views.payment, name='payment'),
    path('addcart/<int:product_id>',views.addcart,name='addcart'),
    path('cart',views.cart,name='cart'),
    path('removecart/<int:product_id>',views.removecart,name='removecart'),
    path('reset_password',views.reset_password,name="reset_password"),
      path('forgot_password/', views.forgot_password, name='forgot_password'),
      path('journals',views.journals,name='journals'),
      path('booking',views.booking,name='booking'),
      path('events',views.events,name='events'),
      path('tickets',views.tickets,name='tickets'),
      path('payments/<float:amount>', views.payments, name='payments'),
      path('event_mpesa_checkout',views.event_mpesa_checkout,name='event_mpesa_checkout'),
    path('event_card_checkout',views.event_CardPayments,name="event_card_checkout"),
    path('redirection',views.redirection,name='redirection'),
    path('redirectionafterticket',views.redirectionafterticket,name='redirectionafterticket'),
    path('download_ticket/<int:ticket_number>',views.download_ticket,name='download_ticket'),
    path('nav',views.nav,name='nav'),
    path('cpanel',views.cpanel,name='cpanel'),
    path('CPANEL',views.CPANEL,name='CPANEL'),
    path('show_ticket',views.show_ticket,name='show_ticket'),
    path('completed-payments/', views.completed_payments_view, name='completed_payments'),


]
