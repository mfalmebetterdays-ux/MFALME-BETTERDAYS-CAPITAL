
from django.http import response
from django.shortcuts import render,redirect,get_object_or_404
import requests
from myapp.models import MfalmeUsers,Payments,Cart,Products,Journals,EventsPayments,AvailableTickets
import logging
from django.http import HttpResponse,JsonResponse
# from intasend import APIService
import json
from django.db.models import Sum
from myapp.notifications import sendsms,sendproductsms ,sendproductsemail,sendemailuser
from django.core.mail import send_mail
from django.conf import settings

from dotenv import load_dotenv
load_dotenv()
import os


# Create your views here.
def index(request):
    user_id=request.session.get('user_id')
    if user_id is  not None:
        user=MfalmeUsers.objects.get(id=user_id)
        product_count=Cart.objects.filter(user=user,status='addedtocart').count()
        return  render(request,'index.html',{'product_count':product_count})
    return render(request,'index.html')

def about(request):
    user_id=request.session.get('user_id')
    if user_id is  not None:
        user=MfalmeUsers.objects.get(id=user_id)
        product_count=Cart.objects.filter(user=user,status='addedtocart').count()
        return render(request,'about.html',{'product_count':product_count})
    return render(request,'about.html')

def login(request):
    return render(request,'login.html')

def services(request):
    user_id=request.session.get('user_id')
    if user_id is  not None:
        user=MfalmeUsers.objects.get(id=user_id)
        product_count=Cart.objects.filter(user=user,status='addedtocart').count()
        return render(request,'services.html',{'product_count':product_count})
    return render(request,'services.html')
def shop(request):
    user_id=request.session.get('user_id')
    if user_id is  not None:
        user=MfalmeUsers.objects.get(id=user_id)
        product_count=Cart.objects.filter(user=user,status='addedtocart').count()
        #get all products and pass to the shop.html
        products=Products.objects.all()
        

        return render(request,'shops.html',{'products':products,'product_count':product_count})
    else:
        products=Products.objects.all()
        

        return render(request,'shops.html',{'products':products})

def cart(request):
    user_id=request.session.get('user_id')
    
    if user_id is  not None:
     #get all products in cart for the logged user and pass to the shop.html
        user=MfalmeUsers.objects.get(id=user_id)
        products=Cart.objects.filter(user=user,status='addedtocart')
        product_count=Cart.objects.filter(user=user,status='addedtocart').count()
        total = Cart.objects.filter(user=user, status='addedtocart').aggregate(total_price=Sum('product__priceusd'))['total_price'] or 0.0
        print("total for my cart is ",total)

        context={
            'products':products,
            'total':total,
            'product_count':product_count

        }

        return render(request,'carts.html',context)
    else:
        return redirect("/login")

def addcart(request,product_id):
    user_id=request.session.get('user_id')
    if user_id is  not None:
        #get product to add
        product=Products.objects.get(id=product_id)

        #get logged in user
        user=MfalmeUsers.objects.get(id=user_id)

        #add object
        cart=Cart.objects.create(user=user,product=product)
        

        return redirect("/shop/")
    else:
        return redirect("/login")
def removecart(request,product_id):
    user_id=request.session.get('user_id')
    if user_id is  not None:
        #get product to add
        product=Products.objects.get(id=product_id)

        #get logged in user
        user=MfalmeUsers.objects.get(id=user_id)

        #add object
        cart=Cart.objects.filter(user=user,product=product).latest('id')
        cart.delete()
        return redirect ("/cart")
    else:
        return redirect("/login/")


def contact(request):
    user_id=request.session.get('user_id')
    if user_id is  not None:
    
        user=MfalmeUsers.objects.get(id=user_id)
        product_count=Cart.objects.filter(user=user,status='addedtocart').count()
        return render(request,'contact.html',{'product_count':product_count})
    return render(request,'contact.html')

def create_account(request):

    password1= request.POST.get('password', False)
    print(password1)
    password2 = request.POST.get('password1', False)
    print(password2)
    email = request.POST.get('email', False)
    print(email)
    phone = request.POST.get('phone', False)
    print(phone)
    username = request.POST.get('username', False)
    print(username)
    


    if  password1 != password2:
        message="the two passwords are diffrent."
        return render(request, "register.html", {"message": message})

        # Check if email and password are provided
    if not email or not password1:
        message="Email and password are required."
        return render(request, "register.html", {"message": message})

        # Check if user already exists
    if MfalmeUsers.objects.filter(email=email).exists():
        
        message="User with this email already exists.."
        return render(request, "register.html", {"message": message})

        # Create user
    user = MfalmeUsers.objects.create(email=email, password=password1,phone=phone,username=username)
    try:
        
       
        return redirect("/login/")
    
    except Exception as e:
        logging.error(f"Failed to send email. Error message: {str(e)}")
        return redirect("/index")
    

        # Respond with success message
    

def login_user(request):
    email = request.POST.get('email',False)
    password = request.POST.get('password',False)

        # Check if an email and password are provided
    if not email or not password:
        
        message= "Email and password are required."
        return render( request,"login.html", {"message": message})

    try:
            # Check if user exists
        user = MfalmeUsers.objects.get(email=email,password=password)
    except MfalmeUsers.DoesNotExist:
        
        message= "User does not exist.You need to sign up please."
        return render(request, "register.html", {"message": message})

        # Check if password is correct
    if user.password != password:
        
        message= "You provided an incorrect password."
        return render(request, "login.html", {"message": message})

        # If everything is correct, respond with user details
    # Store the user ID in the session
    request.session['user_id'] = user.id
    print(user.id)
    return render(request,"index.html",{'user_id':user.id})

def logout(request):
    user_id=request.session.get('user_id')
    if user_id is  not None:
        del request.session['user_id']
        return redirect("/index")
    else:
        return redirect("/index")
    
def login(request):
    return render(request,"login.html")

def register(request):
    return render(request,"register.html")


def mpesa_checkout(request):
     #getting user id from session
    user_id=request.session.get('user_id')
    print(user_id)
    if user_id is not None:
        

        #getting saf number from form
        phone = request.POST.get('phone', False)
        print(phone)
        #email of the user
        email = MfalmeUsers.objects.get(id=user_id).email
        #cost of course
        keprice = request.session.get('keprice')
        print(keprice)
        amountusd = request.session.get('usdprice')
        print(amountusd)
        
        if phone.startswith('0'):
                phone = '254' + phone[1:]
                #print(phone)
                
        payment_instance=Payments.objects.create(mpesa_number=phone,email=email,keprice=keprice,amountusd=amountusd,userId=user_id)
        payment_instance.save()
        

        try:
                # Initialize the APIService
            print("before token")
            token = os.getenv("token")
            print(token)
            publishable_key = os.getenv("publishable_key")
            print(publishable_key)
            print("after token")
            service = APIService(token=token, publishable_key=publishable_key, test=False)
            print("errornot here")

                # Trigger M-Pesa STK Push
            response = service.collect.mpesa_stk_push(phone_number=phone, email=email, amount=keprice,narrative="buyingcourse",api_ref="mfalmepayment")
            print(response)
            
            
            

                # Return the response from the M-Pesa STK Push
            return render(request,"loading.html")

        except Exception as e:
                # Return an error if there's an exception
            return render(request,"index.html",{"error": "try again later "})
    else:
        return redirect('/login')



def CardPayments(request):
    #getting user id from session
    user_id=request.session.get('user_id')
    if user_id is not None:
       

        #getting saf number from form
        #phone = request.POST.get('phone', False)
        #email of the user
        email = MfalmeUsers.objects.get(id=user_id).email
        #cost of course
        amountusd = request.session.get('usdprice')
        
        
                
        payment_instance=Payments.objects.create(email=email,amountusd=amountusd,userId=user_id)
        payment_instance.save()
        

        
        try:
            token = os.getenv("token")
            publishable_key = os.getenv("publishable_key")
            
            service = APIService(token=token, publishable_key=publishable_key, test=False)

            response = service.collect.checkout(email=email, amount=amountusd, currency="USD", api_ref="mfalmepayment", redirect_url="http://example.com/thank-you")
            url=response.get("url")
            print(url)
            
            return redirect(url)

        except:
            return redirect("/index")
    else:
        return redirect("/login")
    
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  
def PaymentCallback(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data in the request."}, status=400)
    print(data)
    

        # Check if transaction state is complete
    if data["state"] == "COMPLETE" and data["api_ref"] =="mfalmepayment":
        account = data["account"]  # Get the account information from data

        # Initialize phone and email variables with None
        phone = None
        email = None

        try:
            int_account = int(account)  # Try converting account to an integer
            phone = (int_account)    # Convert the integer to a character (assuming this is intended for phone number processing)
            print(phone)
        except ValueError:
            # If account is not an integer, treat it as an email
            email = account
            print(email)

        if phone is not None:
            # Process payments based on phone number
            try:
                payment_instance = Payments.objects.filter(mpesa_number=phone).latest('id')
                payment_instance.payment_status = 'completed'
                payment_instance.save()
                print("status saved")

                #get id of the user 
                user_id=payment_instance.userId
                print("user id is ",user_id)
                #get user
                user=MfalmeUsers.objects.get(id=user_id)
                print(user)
                #amount trasacted 

                
                amountusd=payment_instance.amountusd
                print(amountusd)

                
                

                
                try:
                    if amountusd ==200:
                        message=' To join lifetime signals group'
                        sendsms(phone,message)
                        message=f'{phone} has paid for lifetime signals'
                        sendsms(254706286667,message)
                    if amountusd==1000:
                        message='To join Lifetime Mentorship group'
                        sendsms(phone,message)
                        message=f'{phone} has paid for Lifetime Mentorship'
                        sendsms(254706286667,message)
                    if amountusd==10000:
                        message='To join Leveraging Package group'
                        sendsms(phone,message)
                        message=f'{phone} has paid for lifetime signals'
                        sendsms(254706286667,message)
                    else:
                        #get items paid from the cart
                        # Assuming 'user' is the user object for which you want to get the product names
                        items = Cart.objects.filter(user=user)
                        print(items)

                        #update the status of cart items to bought
                        items.update(status='bought')

                        # Extracting product names using list comprehension
                        product_names = [item.product.name for item in items]
                        print(product_names)
                        sendproductsms(phone,product_names)
                    
                    return JsonResponse({'message':'mpesa payment complete'})
                except:
                    return JsonResponse({'message':'mpesa payment complete'})
                

            except Payments.DoesNotExist:
                return JsonResponse({"message": "No payment found for this phone number."})

        elif email is not None:
            # Process payments based on email
            try:
                payment_instance = Payments.objects.filter(email=email).latest('id')
                payment_instance.payment_status = 'completed'
                payment_instance.payment_method = 'card'
                payment_instance.save()

                
                

                
                try:
                    #send_mail(subject, message, from_email, recipient_list)
                    if amountusd ==200:
                        message=' To join lifetime signals group'
                        sendemailuser(email,message)
                        message=f'{phone} has paid for lifetime signals'
                        sendemailuser('info@mfalmebetterdayscapital.com',message)
                    if amountusd==1000:
                        message='To join Lifetime Mentorship group'
                        sendemailuser(email,message)
                        message=f'{phone} has paid for Lifetime Mentorship'
                        sendemailuser('info@mfalmebetterdayscapital.com',message)
                    if amountusd==10000:
                        message='To join Leveraging Package group'
                        sendemailuser(email,message)
                        message=f'{phone} has paid for lifetime signals'
                        sendemailuser('info@mfalmebetterdayscapital.com',message)
                    else:
                        #get items paid from the cart
                        # Assuming 'user' is the user object for which you want to get the product names
                        items = Cart.objects.filter(user=user)

                        #update the status of cart items to bought
                        items.update(status='bought')

                        # Extracting product names using list comprehension
                        product_names = [item.product.name for item in items]

                        sendproductsemail(email,product_names)
                    
                    return JsonResponse({'message':'mpesa payment complete'})
                except:
                    return JsonResponse({'message':'mpesa payment complete'})
                

            except Payments.DoesNotExist:
                return JsonResponse({"message": "No payment found for this email."})

        else:
            return JsonResponse({"message": "No email or phone provided."})

        
    
    
    elif data["state"] == "COMPLETE" and data["api_ref"] =="eventsmfalmepayment":
        account = data["account"]  # Get the account information from data

        # Initialize phone and email variables with None
        phone = None
        email = None

        try:
            int_account = int(account)  # Try converting account to an integer
            phone = (int_account)    # Convert the integer to a character (assuming this is intended for phone number processing)
            print(phone)
        except ValueError:
            # If account is not an integer, treat it as an email
            email = account
            print(email)

        if phone is not None:
            # Process payments based on phone number
            try:
                payment_instance = EventsPayments.objects.filter(mpesa_number=phone).latest('id')
                payment_instance.payment_status = 'completed'
                amountusd=payment_instance.amountusd
                tickets = int(float(amountusd/100))
                payment_instance.no_of_seats=tickets
                ticket_number=payment_instance.tickets_number
                payment_instance.save()
                print("status saved")

                #get id of the user 
                user_id=payment_instance.userId
                print("user id is ",user_id)
                #get user
                user=MfalmeUsers.objects.get(id=user_id)
                print(user)
                #amount trasacted

                
                

                
                try:
                    
                    print("1")
                    available_tickets=get_object_or_404(AvailableTickets, pk=1)
                    print("2")
                    available_tickets.amount= available_tickets.amount -tickets
                    print("3")
                    available_tickets.save()
                    print("1")
                    message=f"We have received your payment of {tickets} tickets.Download  your ticket here https://www.mfalmebetterdayscapital.com/download_ticket/{ticket_number}."
                    print("1")
                    sendsms(phone,message)
                    print("4")
                    message=f"{phone} has purchased {tickets} tickets."
                    print("1")
                    sendsms(254706286667,message)
                    print("6")
                    return JsonResponse({'message':'mpesa payment complete'})
                    
                except:
                    return JsonResponse({'message':'mpesa payment complete'})
                

            except Payments.DoesNotExist:
                return JsonResponse({"message": "No payment found for this phone number."})

        elif email is not None:
            # Process payments based on email
            try:
                payment_instance = EventsPayments.objects.filter(email=email).latest('id')
                payment_instance.payment_status = 'completed'
                payment_instance.payment_method = 'card'
                amountusd=payment_instance.amountusd
                tickets = int(float(amountusd/100))
                ticket_number=payment_instance.tickets_number
                payment_instance.no_of_seats=tickets
                payment_instance.save()

                
                

                
                try:
                    #send_mail(subject, message, from_email, recipient_list)
                    
                    available_tickets=get_object_or_404(AvailableTickets, pk=1)
                    available_tickets.amount= available_tickets.amount -tickets
                    available_tickets.save()
                    message=f"We have received your payment of {tickets} tickets.View your ticket here https://www.mfalmebetterdayscapital.com/download_ticket/{ticket_number}."
                    sendemailuser(email,message)
                    message=f'{phone} has purchased ',tickets ,'tickets'
                    sendemailuser('info@mfalmebetterdayscapital.com',message)
                    return JsonResponse({'message':'mpesa payment complete'})
                    
                    
                        
                    
                    
                except:
                    return JsonResponse({'message':'mpesa payment complete'})
                

            except Payments.DoesNotExist:
                return JsonResponse({"message": "No payment found for this email."})

        else:
            return JsonResponse({"message": "No email or phone provided."})

        
    else:
        return JsonResponse({"message": "Transaction state is not complete."})
    
def payment(request,amount):
    user_id=request.session.get('user_id')
    

    if user_id is not None:

        usdprice=amount
        keprice=int(amount*135)
            
        request.session['usdprice'] = usdprice
        request.session['keprice'] = keprice
        return render(request,"payment.html",{"usdprice":usdprice})
    else:
        return redirect("/login")
def payments(request,amount):
    user_id=request.session.get('user_id')
    

    if user_id is not None:

        usdprice=amount
        keprice=int(amount*130)
            
        request.session['usdprice'] = usdprice
        request.session['keprice'] = keprice
        return render(request,"payments.html",{"usdprice":usdprice})
    else:
        return redirect("/login")

    
def reset_password(request):
    email = request.POST.get('email',False)
    print(email)
    try:
        
        password=MfalmeUsers.objects.get(email=email).password
        subject = 'Your password'
        message = '''Your password is {}..'''.format(password) 
        from_email = settings.EMAIL_HOST_USER   
        recipient_list = [email]
        print("sending email")
        send_mail(subject, message, from_email, recipient_list)
        print('email sent ')
        message="your password has been sent to your email"
        return render(request,"forgot_password.html",{"message":message})
    except Exception as e:
        logging.error(f"Failed to send email. Error message: {str(e)}")
        message='use the correct email'
        return render(request,"forgot_password.html",{"message":message})
def forgot_password(request):
    return render(request,'forgot_password.html')

def journals(request):
    user_id=request.session.get('user_id')
    if user_id is not None:
        user=MfalmeUsers.objects.get(id=user_id)
        product_count=Cart.objects.filter(user=user,status='addedtocart').count()
        #get all the videos
        videos=Journals.objects.all()
        #pass the videos to the journals template

        return render (request,'journal.html',{'videos':videos,'product_count':product_count})
    else:
        
        #get all the videos
        videos=Journals.objects.all()
        #pass the videos to the journals template

        return render (request,'journal.html',{'videos':videos})

def booking (request):
    phone = request.POST.get('phone',False)
    package = request.POST.get('package',False)
    name = request.POST.get('name',False)
    message = request.POST.get('message',False)
    sender=settings.EMAIL_HOST_USER
    recipients = ['info@mfalmebetterdayscapital.com']
    subject="message from  "  + name
    print(subject)
    message=f'{name} chose  {package}.\n\nPhone: {phone}\nMessage: {message}'
    
    

    try:
        send_mail(subject, message, sender, recipients)

        print('Your message has been sent successfully.')
        return redirect('/index')  # Redirect to a success page or some other page
    except Exception as e:
        print('An error occurred: {e}')
        return redirect('/index')
    
def events(request):
    return render(request,'events.html')

def tickets(request):
    
    tickets_available = get_object_or_404(AvailableTickets, pk=1)
    tickets_available=tickets_available.amount
    return render(request,'tickets.html',{"tickets_available":tickets_available})

def event_mpesa_checkout(request):
     #getting user id from session
    user_id=request.session.get('user_id')
    print(user_id)
    if user_id is not None:
        

        #getting saf number from form
        phone = request.POST.get('phone', False)
        print(phone)
        #email of the user
        email = MfalmeUsers.objects.get(id=user_id).email
        #cost of course
        keprice = request.session.get('keprice')
        print(keprice)
        amountusd = request.session.get('usdprice')
        print(amountusd)
        
        if phone.startswith('0'):
                phone = '254' + phone[1:]
                #print(phone)
                
        payment_instance=EventsPayments.objects.create(mpesa_number=phone,email=email,keprice=keprice,amountusd=amountusd,userId=user_id)
        payment_instance.save()
        

        try:
                # Initialize the APIService
            print("before token")
            token = os.getenv("token")
            print(token)
            publishable_key = os.getenv("publishable_key")
            print(publishable_key)
            print("after token")
            service = APIService(token=token, publishable_key=publishable_key, test=False)
            print("errornot here")

                # Trigger M-Pesa STK Push
            response = service.collect.mpesa_stk_push(phone_number=phone, email=email, amount=keprice,narrative="buyingticket",api_ref="eventsmfalmepayment")
            print(response)
            
            
            

                # Return the response from the M-Pesa STK Push
            return render(request,"buyingticketloader.html")

        except Exception as e:
                # Return an error if there's an exception
            return render(request,"index.html",{"error": "try again later "})
    else:
        return redirect('/login')



def event_CardPayments(request):
    #getting user id from session
    user_id=request.session.get('user_id')
    if user_id is not None:
       

        #getting saf number from form
        #phone = request.POST.get('phone', False)
        #email of the user
        email = MfalmeUsers.objects.get(id=user_id).email
        #cost of course
        amountusd = request.session.get('usdprice')
        
        
                
        payment_instance=EventsPayments.objects.create(email=email,amountusd=amountusd,userId=user_id)
        payment_instance.save()
        

        
        try:
            token = os.getenv("token")
            publishable_key = os.getenv("publishable_key")
            
            service = APIService(token=token, publishable_key=publishable_key, test=False)

            response = service.collect.checkout(email=email, amount=amountusd, currency="USD", api_ref="eventsmfalmepayment", redirect_url="http://example.com/thank-you")
            url=response.get("url")
            print(url)
            
            return redirect(url)

        except:
            return redirect("/index")
    else:
        return redirect("/login")

def redirection(request):
    user_id=request.session.get('user_id')
    if user_id is not None:
        from datetime import datetime, timedelta
        from django.utils import timezone
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        purchases=Cart.objects.filter(user=user_id,status='bought',timestamp__gte=today_start,timestamp__lt=today_end)
        product_ids = purchases.values_list('product', flat=True)

        # Query all products using the extracted product IDs
        products = Products.objects.filter(id__in=product_ids)



        return render (request,"redirection.html",{"products":products})
    return redirect("/login")

def download_ticket(request,ticket_number):
    
    
    ticket_instance=EventsPayments.objects.get(tickets_number=ticket_number)
    
    
    price=ticket_instance.no_of_seats * 100
    context={
            "ticket_instance":ticket_instance,
            
            "price":price
            

        }
    return render(request,'download_ticket.html', context)
       
    

def nav(request):
    return render(request,"nav.html")


def redirectionafterticket(request):
    return render (request,"afterticketredirection.html")

def cpanel(request):
    return redirect ("https://mfalmebetterdayscapital.com/cpanel")

def CPANEL(request):
    return redirect ("https://mfalmebetterdayscapital.com/cpanel")

def show_ticket(request):
    price=200
    return render(request,'show_ticket.html',{'price':price})

from django.db.models import Q 

def completed_payments_view(request):
    # Filter payments where payment_status is 'completed' 
    # and either keprice > 10000 or amountusd > 90
    payments = EventsPayments.objects.filter(
        payment_status='completed'
    ).filter(
        Q(keprice__gt=10000) | Q(amountusd__gt=90)
    )
    
    context = {
        'payments': payments
    }
    
    return render(request, 'completed_payments.html', context)
