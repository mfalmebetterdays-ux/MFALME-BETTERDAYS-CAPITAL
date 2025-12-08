
from django.contrib import admin
from . models import MfalmeUsers,Payments,Cart,Products,Journals,AvailableTickets,EventsPayments





# Register your models here.
admin.site.register(MfalmeUsers)
admin.site.register(Products)
admin.site.register(Payments)
admin.site.register(Cart)
admin.site.register(Journals)
admin.site.register(AvailableTickets)
admin.site.register(EventsPayments)