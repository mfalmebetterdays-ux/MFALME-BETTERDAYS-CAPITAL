
from django.db import models
from django.utils.timezone import now

# Create your models here.
#users model
class MfalmeUsers (models.Model):
    email=models.EmailField()
    password=models.TextField() 
    username=models.CharField(max_length=30)
    phone=models.CharField(max_length=30)
    

    def __str__(self):
        return f'{self.email} :{self.username}'
    
class Payments(models.Model):
    email=models.EmailField()
    userId = models.IntegerField()
    amountusd = models.FloatField(default=0.0)
    keprice = models.FloatField(default=0.0)
    mpesa_number = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(max_length=20,default='initialized')
    payment_method = models.CharField(max_length=20,default='mpesa')

    def __str__(self):
        return f'{self.userId} :{self.payment_status} :{self.payment_method}'

class Products(models.Model):
    name=models.CharField(max_length=20)
    product_image=models.URLField()
    priceusd = models.FloatField(default=0.0)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} :{self.priceusd}'
    
class Cart(models.Model):
    product=models.ForeignKey('Products', related_name='productid', on_delete=models.CASCADE)
    user=models.ForeignKey('MfalmeUsers', related_name='userid', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    status=models.CharField(max_length=20,default='addedtocart')

class Journals(models.Model):
    video_url=models.URLField()
    timestamp = models.DateField(auto_now_add=True)

    def __str__(self):
        return (self.video_url)
    
class EventsPayments(models.Model):
    email=models.EmailField()
    userId = models.IntegerField()
    amountusd = models.FloatField(default=0.0)
    keprice = models.FloatField(default=0.0)
    mpesa_number = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(max_length=20,default='initialized')
    payment_method = models.CharField(max_length=20,default='mpesa')
    no_of_seats=models.IntegerField(default=0,null=True)
    tickets_number=models.IntegerField(default=0,null=True)

    @staticmethod
    def get_next_tickets_number():
        last_payment = EventsPayments.objects.all().order_by('-id').first()
        if last_payment:
            return int(float(last_payment.tickets_number))  + 11
        else:
            return 11

    def save(self, *args, **kwargs):
        if not self.pk:  # Only set tickets_number for new instances
            self.tickets_number = self.get_next_tickets_number()
            
        super(EventsPayments, self).save(*args, **kwargs)

class AvailableTickets(models.Model):
    amount=models.IntegerField()


    


