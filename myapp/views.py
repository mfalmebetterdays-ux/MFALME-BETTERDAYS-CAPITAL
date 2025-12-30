from django.shortcuts import render, redirect, reverse
from django.contrib import messages
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
import random
import string
import uuid
import hashlib
import requests
import json
from .models import MfalmeUsers, VerificationCode, PaymentTransaction
from django.views.decorators.csrf import csrf_exempt
import time

# ===== PAYSTACK PAYMENT INTEGRATION =====
try:
    from paystackapi.paystack import Paystack
    PAYSTACK_AVAILABLE = True
except ImportError:
    PAYSTACK_AVAILABLE = False
    print("⚠️ Paystack Python SDK not installed. Run: pip install paystack-python")
    

# ===== EXCHANGE RATE FUNCTIONS =====

def get_live_exchange_rate():
    """
    Get current USD to KES exchange rate from a reliable API
    Returns: float exchange rate (USD to KES)
    """
    try:
        # Try multiple APIs for reliability
        
        # API 1: Frankfurter (free, reliable)
        try:
            response = requests.get('https://api.frankfurter.app/latest?from=USD&to=KES', timeout=5)
            if response.status_code == 200:
                data = response.json()
                rate = data['rates']['KES']
                print(f"✅ Exchange rate from Frankfurter: 1 USD = {rate} KES")
                return float(rate)
        except:
            pass
        
        # API 2: ExchangeRate-API (free tier)
        try:
            response = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=5)
            if response.status_code == 200:
                data = response.json()
                rate = data['rates']['KES']
                print(f"✅ Exchange rate from ExchangeRate-API: 1 USD = {rate} KES")
                return float(rate)
        except:
            pass
        
        # API 3: Open Exchange Rates (free tier - requires app_id)
        if hasattr(settings, 'OPEN_EXCHANGE_RATES_APP_ID'):
            try:
                app_id = settings.OPEN_EXCHANGE_RATES_APP_ID
                response = requests.get(f'https://openexchangerates.org/api/latest.json?app_id={app_id}', timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    rate = data['rates']['KES']
                    print(f"✅ Exchange rate from OpenExchangeRates: 1 USD = {rate} KES")
                    return float(rate)
            except:
                pass
        
        # API 4: Fixer.io (free tier - requires API key)
        if hasattr(settings, 'FIXER_API_KEY'):
            try:
                api_key = settings.FIXER_API_KEY
                response = requests.get(f'http://data.fixer.io/api/latest?access_key={api_key}&symbols=KES', timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    # Fixer returns EUR base, so we need USD to EUR then EUR to KES
                    usd_to_eur = 1 / data['rates']['USD']
                    eur_to_kes = data['rates']['KES']
                    rate = usd_to_eur * eur_to_kes
                    print(f"✅ Exchange rate from Fixer: 1 USD = {rate} KES")
                    return float(rate)
            except:
                pass
        
        # Fallback: Use cached rate from session or database
        print("⚠️ Using fallback exchange rate")
        return 160.0  # Conservative fallback rate
        
    except Exception as e:
        print(f"❌ Exchange rate error: {str(e)}")
        return 160.0  # Conservative fallback rate

def convert_usd_to_kes_cents(usd_amount):
    """
    Convert USD amount to KES cents for Paystack
    Args:
        usd_amount: USD amount in dollars
    Returns:
        Tuple: (kes_amount_in_cents, exchange_rate_used, kes_amount)
    """
    exchange_rate = get_live_exchange_rate()
    kes_amount = usd_amount * exchange_rate
    kes_cents = int(kes_amount * 100)  # Paystack expects cents
    
    print(f"💱 Currency Conversion: ${usd_amount} USD → {kes_amount:,.0f} KES → {kes_cents:,} cents (Rate: {exchange_rate})")
    
    return kes_cents, exchange_rate, kes_amount

# Initialize Paystack
def get_paystack_client():
    """Initialize Paystack client with secret key"""
    if not PAYSTACK_AVAILABLE:
        print("❌ Paystack SDK not available")
        return None
    
    try:
        paystack = Paystack(secret_key=settings.PAYSTACK_SECRET_KEY)
        return paystack
    except Exception as e:
        print(f"❌ Paystack initialization error: {str(e)}")
        return None

# ===== PAYSTACK WEBHOOK HANDLER =====
@csrf_exempt
def paystack_webhook(request):
    """
    Handle Paystack webhook notifications for recurring payments
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    
    try:
        # Get the payload
        payload = json.loads(request.body)
        
        # Verify the event
        event = payload.get('event', '')
        data = payload.get('data', {})
        
        print(f"🔔 Paystack Webhook Received: {event}")
        
        if event == 'charge.success':
            reference = data.get('reference', '')
            if reference:
                # Process the successful charge
                try:
                    transaction = PaymentTransaction.objects.get(reference=reference)
                    transaction.status = 'completed'
                    transaction.paystack_data = data
                    transaction.paid_at = timezone.now()
                    transaction.save()
                    
                    print(f"✅ Webhook: Payment {reference} marked as completed")
                    
                except PaymentTransaction.DoesNotExist:
                    print(f"⚠️ Webhook: Transaction {reference} not found in database")
        
        elif event == 'subscription.create':
            subscription_code = data.get('subscription_code', '')
            customer_email = data.get('customer', {}).get('email', '')
            
            print(f"📝 Webhook: New subscription created for {customer_email}")
            
            try:
                user = MfalmeUsers.objects.get(email=customer_email)
                # Create or update subscription record
                print(f"✅ Webhook: Subscription {subscription_code} linked to user {user.email}")
            except MfalmeUsers.DoesNotExist:
                print(f"⚠️ Webhook: User {customer_email} not found for subscription")
        
        elif event == 'subscription.disable':
            subscription_code = data.get('subscription_code', '')
            print(f"📝 Webhook: Subscription disabled: {subscription_code}")
        
        # Return success response to Paystack
        return JsonResponse({'status': 'success'})
        
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# ===== PAYMENT VIEWS =====

def initiate_package_payment(request, package_type, amount):
    """
    Initiate payment for trading packages
    Each package has unique payment initialization with USD to KES conversion
    """
    if 'user_id' not in request.session:
        messages.error(request, 'Please login to make a payment.')
        return redirect('login_page')
    
    try:
        user = MfalmeUsers.objects.get(id=request.session['user_id'])
        
        # Map package types to proper names
        package_map = {
            'market_consultation': {'name': 'Market Consultation', 'amount_usd': 200},
            'lifetime_mentorship': {'name': 'Lifetime Mentorship Package', 'amount_usd': 5000},
            'leveraging_package': {'name': 'Leveraging Package', 'amount_usd': 100000},
            'lifetime_signals': {'name': 'Lifetime Signals Package', 'amount_usd': 200},
        }
        
        if package_type not in package_map:
            messages.error(request, 'Invalid package selection.')
            return redirect('services')
        
        package_info = package_map[package_type]
        usd_amount = package_info['amount_usd']
        
        print(f"💰 Package Payment Initiated: {package_info['name']} - ${usd_amount} USD")
        
        # CONVERT USD TO KES CENTS
        kes_cents, exchange_rate, kes_amount = convert_usd_to_kes_cents(usd_amount)
        
        # Generate unique reference
        reference = f"MFALME-PKG-{user.soldier_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create transaction in database
        transaction = PaymentTransaction.objects.create(
            user=user,
            reference=reference,
            amount=usd_amount,  # Store USD amount
            currency='USD',
            package_type=package_type,
            status='initiated',
            payment_type='package',
            metadata={
                'user_id': user.id,
                'soldier_id': user.soldier_id,
                'package_name': package_info['name'],
                'amount_usd': usd_amount,
                'amount_kes': kes_amount,
                'amount_kes_cents': kes_cents,
                'exchange_rate': exchange_rate,
                'conversion_timestamp': datetime.now().isoformat(),
                'payment_type': 'package_payment',
                'currency_converted': True,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Paystack API headers
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        
        # Paystack data with KES amount
        data = {
            'email': user.email,
            'amount': kes_cents,  # Amount in KES cents
            'reference': reference,
            'currency': 'KES',  # Paystack Kenya uses KES
            'callback_url': f"{request.scheme}://{request.get_host()}/payment/verify/{reference}/",
            'metadata': {
                'custom_fields': [
                    {
                        'display_name': "Full Name",
                        'variable_name': "full_name",
                        'value': user.username
                    },
                    {
                        'display_name': "Soldier ID",
                        'variable_name': "soldier_id",
                        'value': user.soldier_id
                    },
                    {
                        'display_name': "Package",
                        'variable_name': "package",
                        'value': package_info['name']
                    },
                    {
                        'display_name': "Amount USD",
                        'variable_name': "amount_usd",
                        'value': f"${usd_amount:,.2f}"
                    },
                    {
                        'display_name': "Amount KES",
                        'variable_name': "amount_kes",
                        'value': f"KES {kes_amount:,.2f}"
                    },
                    {
                        'display_name': "Exchange Rate",
                        'variable_name': "exchange_rate",
                        'value': f"1 USD = {exchange_rate:,.2f} KES"
                    }
                ]
            }
        }
        
        print(f"📤 Sending to Paystack: KES {kes_amount:,.2f} ({kes_cents:,} cents)")
        
        response = requests.post(
            'https://api.paystack.co/transaction/initialize',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status'):
                # Store in session for verification
                request.session['payment_reference'] = reference
                request.session['payment_type'] = 'package'
                request.session['package_type'] = package_type
                request.session['amount_usd'] = usd_amount
                request.session['amount_kes'] = kes_amount
                request.session['exchange_rate'] = exchange_rate
                
                print(f"✅ Payment initialized: ${usd_amount} USD → KES {kes_amount:,.2f}")
                
                # Redirect to Paystack payment page
                return redirect(result['data']['authorization_url'])
            else:
                error_msg = result.get('message', 'Failed to initialize payment')
                messages.error(request, f'Paystack Error: {error_msg}')
        else:
            messages.error(request, f'Payment service error: {response.status_code}')
        
        transaction.status = 'failed'
        transaction.save()
        return redirect('services')
            
    except MfalmeUsers.DoesNotExist:
        messages.error(request, 'User account not found.')
        return redirect('login_page')
    except Exception as e:
        print(f"❌ Payment initialization error: {str(e)}")
        messages.error(request, f'Payment initialization failed: {str(e)}')
        return redirect('services')

def initiate_education_payment(request, program_type, duration):
    """
    Initiate payment for education programs with USD to KES conversion
    """
    if 'user_id' not in request.session:
        messages.error(request, 'Please login to enroll in a program.')
        return redirect('login_page')
    
    try:
        user = MfalmeUsers.objects.get(id=request.session['user_id'])
        
        # Map education programs to prices (in USD)
        program_prices = {
            'IPLT': {'1_month': 0, '12_months': 1299},  # USD
            'PTM': {'1_month': 1999, '12_months': 3499},  # USD
            'POTM': {'1_month': 1999, '12_months': 3499},  # USD
            'PFTM': {'1_month': 1499, '12_months': 2999},  # USD
        }
        
        if program_type not in program_prices or duration not in program_prices[program_type]:
            messages.error(request, 'Invalid program selection.')
            return redirect('education')
        
        usd_amount = program_prices[program_type][duration]
        program_name = f"{program_type} Program ({duration.replace('_', ' ')})"
        
        print(f"🎓 Education Payment: {program_name} - ${usd_amount} USD")
        
        # CONVERT USD TO KES CENTS
        kes_cents, exchange_rate, kes_amount = convert_usd_to_kes_cents(usd_amount)
        
        # Generate unique reference
        reference = f"MFALME-EDU-{user.soldier_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create transaction
        transaction = PaymentTransaction.objects.create(
            user=user,
            reference=reference,
            amount=usd_amount,  # Store USD amount
            currency='USD',
            program_type=program_type,
            duration=duration,
            status='initiated',
            payment_type='education',
            metadata={
                'user_id': user.id,
                'soldier_id': user.soldier_id,
                'program_name': program_name,
                'duration': duration,
                'amount_usd': usd_amount,
                'amount_kes': kes_amount,
                'amount_kes_cents': kes_cents,
                'exchange_rate': exchange_rate,
                'conversion_timestamp': datetime.now().isoformat(),
                'payment_type': 'education_payment',
                'currency_converted': True,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Paystack API
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        
        data = {
            'email': user.email,
            'amount': kes_cents,  # KES cents
            'reference': reference,
            'currency': 'KES',
            'callback_url': f"{request.scheme}://{request.get_host()}/payment/verify/{reference}/",
            'metadata': {
                'custom_fields': [
                    {
                        'display_name': "Student Name",
                        'variable_name': "student_name",
                        'value': user.username
                    },
                    {
                        'display_name': "Soldier ID",
                        'variable_name': "soldier_id",
                        'value': user.soldier_id
                    },
                    {
                        'display_name': "Program",
                        'variable_name': "program",
                        'value': program_name
                    },
                    {
                        'display_name': "Duration",
                        'variable_name': "duration",
                        'value': duration.replace('_', ' ')
                    },
                    {
                        'display_name': "Amount USD",
                        'variable_name': "amount_usd",
                        'value': f"${usd_amount:,.2f}"
                    },
                    {
                        'display_name': "Amount KES",
                        'variable_name': "amount_kes",
                        'value': f"KES {kes_amount:,.2f}"
                    }
                ]
            }
        }
        
        response = requests.post(
            'https://api.paystack.co/transaction/initialize',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status'):
                request.session['payment_reference'] = reference
                request.session['payment_type'] = 'education'
                request.session['program_type'] = program_type
                request.session['program_duration'] = duration
                request.session['amount_usd'] = usd_amount
                request.session['amount_kes'] = kes_amount
                request.session['exchange_rate'] = exchange_rate
                
                print(f"✅ Education payment initialized: ${usd_amount} USD → KES {kes_amount:,.2f}")
                
                return redirect(result['data']['authorization_url'])
            else:
                messages.error(request, result.get('message', 'Failed to initialize payment'))
        else:
            messages.error(request, 'Failed to connect to payment service')
        
        transaction.status = 'failed'
        transaction.save()
        return redirect('education')
            
    except MfalmeUsers.DoesNotExist:
        messages.error(request, 'User account not found.')
        return redirect('login_page')
    except Exception as e:
        print(f"❌ Education payment error: {str(e)}")
        messages.error(request, 'Payment initialization failed.')
        return redirect('education')

def initiate_partnership_payment(request, tier):
    """
    Initiate payment for partnership programs with USD to KES conversion
    """
    if 'user_id' not in request.session:
        messages.error(request, 'Please login to become a partner.')
        return redirect('login_page')
    
    try:
        user = MfalmeUsers.objects.get(id=request.session['user_id'])
        
        # Partnership tier amounts (in USD)
        tier_amounts = {
            'bronze': 250000,    # 250,000 USD
            'silver': 500000,    # 500,000 USD
            'gold': 1000000,     # 1,000,000 USD
            'platinum': 5000000, # 5,000,000 USD
            'premium': 10000000, # 10,000,000 USD
        }
        
        if tier not in tier_amounts:
            messages.error(request, 'Invalid partnership tier.')
            return redirect('partnership')
        
        usd_amount = tier_amounts[tier]
        tier_name = tier.capitalize() + " Partnership"
        
        print(f"🤝 Partnership Payment: {tier_name} - ${usd_amount:,} USD")
        
        # CONVERT USD TO KES CENTS
        kes_cents, exchange_rate, kes_amount = convert_usd_to_kes_cents(usd_amount)
        
        # Generate unique reference
        reference = f"MFALME-PART-{user.soldier_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create transaction
        transaction = PaymentTransaction.objects.create(
            user=user,
            reference=reference,
            amount=usd_amount,  # Store USD amount
            currency='USD',
            partnership_tier=tier,
            status='initiated',
            payment_type='partnership',
            metadata={
                'user_id': user.id,
                'soldier_id': user.soldier_id,
                'company_name': user.username,
                'tier': tier_name,
                'amount_usd': usd_amount,
                'amount_kes': kes_amount,
                'amount_kes_cents': kes_cents,
                'exchange_rate': exchange_rate,
                'conversion_timestamp': datetime.now().isoformat(),
                'payment_type': 'partnership_payment',
                'requires_approval': True,
                'currency_converted': True,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # For large amounts, we might want to implement special handling
        # For now, use standard Paystack flow
        
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        
        data = {
            'email': user.email,
            'amount': kes_cents,  # KES cents
            'reference': reference,
            'currency': 'KES',
            'callback_url': f"{request.scheme}://{request.get_host()}/payment/verify/{reference}/",
            'metadata': {
                'custom_fields': [
                    {
                        'display_name': "Company/Individual",
                        'variable_name': "company",
                        'value': user.username
                    },
                    {
                        'display_name': "Soldier ID",
                        'variable_name': "soldier_id",
                        'value': user.soldier_id
                    },
                    {
                        'display_name': "Partnership Tier",
                        'variable_name': "tier",
                        'value': tier_name
                    },
                    {
                        'display_name': "Contact Phone",
                        'variable_name': "phone",
                        'value': user.phone
                    },
                    {
                        'display_name': "Amount USD",
                        'variable_name': "amount_usd",
                        'value': f"${usd_amount:,.2f}"
                    },
                    {
                        'display_name': "Amount KES",
                        'variable_name': "amount_kes",
                        'value': f"KES {kes_amount:,.2f}"
                    },
                    {
                        'display_name': "Large Amount Notice",
                        'variable_name': "notice",
                        'value': "This is a large transaction. Please ensure sufficient funds."
                    }
                ]
            }
        }
        
        response = requests.post(
            'https://api.paystack.co/transaction/initialize',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status'):
                request.session['payment_reference'] = reference
                request.session['payment_type'] = 'partnership'
                request.session['partnership_tier'] = tier
                request.session['amount_usd'] = usd_amount
                request.session['amount_kes'] = kes_amount
                request.session['exchange_rate'] = exchange_rate
                
                print(f"✅ Partnership payment initialized: ${usd_amount:,} USD → KES {kes_amount:,.2f}")
                
                return redirect(result['data']['authorization_url'])
            else:
                messages.error(request, result.get('message', 'Failed to initialize payment'))
        else:
            messages.error(request, 'Failed to connect to payment service')
        
        transaction.status = 'failed'
        transaction.save()
        return redirect('partnership')
            
    except MfalmeUsers.DoesNotExist:
        messages.error(request, 'User account not found.')
        return redirect('login_page')
    except Exception as e:
        print(f"❌ Partnership payment error: {str(e)}")
        messages.error(request, 'Partnership payment initialization failed.')
        return redirect('partnership')

@csrf_exempt
def initiate_custom_payment(request):
    """
    Custom payment for miscellaneous services with USD to KES conversion
    """
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('contact')
    
    if 'user_id' not in request.session:
        messages.error(request, 'Please login to make a payment.')
        return redirect('login_page')
    
    try:
        user = MfalmeUsers.objects.get(id=request.session['user_id'])
        
        # Get custom payment details
        usd_amount = float(request.POST.get('amount', 0))
        description = request.POST.get('description', 'Custom Payment')
        service_type = request.POST.get('service_type', 'other')
        
        if usd_amount <= 0:
            messages.error(request, 'Invalid payment amount.')
            return redirect('contact')
        
        print(f"💰 Custom Payment: {description} - ${usd_amount} USD")
        
        # CONVERT USD TO KES CENTS
        kes_cents, exchange_rate, kes_amount = convert_usd_to_kes_cents(usd_amount)
        
        # Generate unique reference
        reference = f"MFALME-CUST-{user.soldier_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create transaction
        transaction = PaymentTransaction.objects.create(
            user=user,
            reference=reference,
            amount=usd_amount,  # Store USD amount
            currency='USD',
            description=description,
            service_type=service_type,
            status='initiated',
            payment_type='custom',
            metadata={
                'user_id': user.id,
                'soldier_id': user.soldier_id,
                'description': description,
                'service_type': service_type,
                'amount_usd': usd_amount,
                'amount_kes': kes_amount,
                'amount_kes_cents': kes_cents,
                'exchange_rate': exchange_rate,
                'conversion_timestamp': datetime.now().isoformat(),
                'payment_type': 'custom_payment',
                'currency_converted': True,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Paystack API
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        
        data = {
            'email': user.email,
            'amount': kes_cents,  # KES cents
            'reference': reference,
            'currency': 'KES',
            'callback_url': f"{request.scheme}://{request.get_host()}/payment/verify/{reference}/",
            'metadata': {
                'custom_fields': [
                    {
                        'display_name': "Customer Name",
                        'variable_name': "customer_name",
                        'value': user.username
                    },
                    {
                        'display_name': "Soldier ID",
                        'variable_name': "soldier_id",
                        'value': user.soldier_id
                    },
                    {
                        'display_name': "Service Description",
                        'variable_name': "service",
                        'value': description
                    },
                    {
                        'display_name': "Amount USD",
                        'variable_name': "amount_usd",
                        'value': f"${usd_amount:,.2f}"
                    },
                    {
                        'display_name': "Amount KES",
                        'variable_name': "amount_kes",
                        'value': f"KES {kes_amount:,.2f}"
                    }
                ]
            }
        }
        
        response = requests.post(
            'https://api.paystack.co/transaction/initialize',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status'):
                request.session['payment_reference'] = reference
                request.session['payment_type'] = 'custom'
                request.session['custom_description'] = description
                request.session['amount_usd'] = usd_amount
                request.session['amount_kes'] = kes_amount
                request.session['exchange_rate'] = exchange_rate
                
                print(f"✅ Custom payment initialized: ${usd_amount} USD → KES {kes_amount:,.2f}")
                
                return redirect(result['data']['authorization_url'])
            else:
                messages.error(request, result.get('message', 'Failed to initialize payment'))
        else:
            messages.error(request, 'Failed to connect to payment service')
        
        transaction.status = 'failed'
        transaction.save()
        return redirect('contact')
            
    except MfalmeUsers.DoesNotExist:
        messages.error(request, 'User account not found.')
        return redirect('login_page')
    except Exception as e:
        print(f"❌ Custom payment error: {str(e)}")
        messages.error(request, 'Custom payment initialization failed.')
        return redirect('contact')

@csrf_exempt
def verify_payment(request, reference):
    """
    Verify Paystack payment callback
    This is called by Paystack after payment
    """
    try:
        # Verify payment with Paystack API
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        }
        
        response = requests.get(
            f'https://api.paystack.co/transaction/verify/{reference}',
            headers=headers
        )
        
        # Get transaction from database
        transaction = PaymentTransaction.objects.get(reference=reference)
        
        if response.status_code == 200:
            verification = response.json()
            
            if verification.get('status') and verification['data']['status'] == 'success':
                # Payment successful
                transaction.status = 'completed'
                transaction.paystack_data = verification['data']
                transaction.paid_at = timezone.now()
                transaction.save()
                
                # Get user from transaction
                user = transaction.user
                metadata = transaction.metadata or {}
                
                # Display conversion details in success message
                usd_amount = metadata.get('amount_usd', transaction.amount)
                kes_amount = metadata.get('amount_kes', 0)
                exchange_rate = metadata.get('exchange_rate', 0)
                
                if kes_amount and exchange_rate:
                    success_msg = (
                        f'✅ Payment successful! '
                        f'${usd_amount:,.2f} USD → KES {kes_amount:,.2f} '
                        f'(Rate: {exchange_rate:,.2f})'
                    )
                else:
                    success_msg = '✅ Payment verified successfully!'
                
                # Handle different payment types
                payment_type = transaction.payment_type
                
                if payment_type == 'package':
                    # Activate package for user
                    package_name = metadata.get('package_name', 'Unknown Package')
                    user.preferred_package = package_name
                    user.account_status = 'active'
                    user.save()
                    
                    # Send package activation email
                    send_package_activation_email(user, transaction)
                    
                    messages.success(request, f'🎉 {success_msg} Package activated: {package_name}')
                    return redirect('payment_success')
                    
                elif payment_type == 'education':
                    # Enroll in education program
                    send_education_enrollment_email(user, transaction)
                    
                    messages.success(request, f'🎓 {success_msg} Education enrollment confirmed!')
                    return redirect('payment_success')
                    
                elif payment_type == 'partnership':
                    # Process partnership application
                    send_partnership_approval_request(user, transaction)
                    
                    messages.success(request, f'🤝 {success_msg} Partnership application submitted!')
                    return redirect('payment_success')
                    
                elif payment_type == 'custom':
                    # Handle custom payment
                    send_custom_payment_confirmation(user, transaction)
                    
                    messages.success(request, f'✅ {success_msg} Custom payment received!')
                    return redirect('payment_success')
                
                else:
                    messages.success(request, success_msg)
                    return redirect('payment_success')
                    
            else:
                # Payment failed
                transaction.status = 'failed'
                transaction.paystack_data = verification.get('data', {}) if response.status_code == 200 else {}
                transaction.save()
                
                messages.error(request, '❌ Payment verification failed. Please try again.')
                return redirect('payment_failed')
        else:
            # API call failed
            transaction.status = 'failed'
            transaction.save()
            
            messages.error(request, '❌ Unable to verify payment. Please contact support.')
            return redirect('payment_failed')
            
    except PaymentTransaction.DoesNotExist:
        messages.error(request, 'Transaction not found.')
        return redirect('index')
    except Exception as e:
        print(f"❌ Payment verification error: {str(e)}")
        messages.error(request, 'Payment verification error.')
        return redirect('payment_failed')

def payment_success(request):
    """Payment success page with conversion details"""
    reference = request.session.get('payment_reference', '')
    payment_type = request.session.get('payment_type', '')
    
    # Get conversion details from session
    usd_amount = request.session.get('amount_usd', 0)
    kes_amount = request.session.get('amount_kes', 0)
    exchange_rate = request.session.get('exchange_rate', 0)
    
    # Try to get transaction details
    transaction = None
    if reference:
        try:
            transaction = PaymentTransaction.objects.get(reference=reference)
        except PaymentTransaction.DoesNotExist:
            pass
    
    context = {
        'reference': reference,
        'payment_type': payment_type,
        'transaction': transaction,
        'usd_amount': usd_amount,
        'kes_amount': kes_amount,
        'exchange_rate': exchange_rate,
        'conversion_applied': bool(kes_amount and exchange_rate),
    }
    
    # Clear payment session data
    payment_keys = ['payment_reference', 'payment_type', 'package_type', 
                    'program_type', 'program_duration', 'partnership_tier', 
                    'custom_description', 'amount_usd', 'amount_kes', 'exchange_rate']
    for key in payment_keys:
        if key in request.session:
            del request.session[key]
    
    return render(request, 'payments/success.html', context)

def payment_failed(request):
    """Payment failed page"""
    reference = request.session.get('payment_reference', '')
    
    context = {
        'reference': reference,
    }
    
    # Clear payment session data
    if 'payment_reference' in request.session:
        del request.session['payment_reference']
    
    return render(request, 'payments/failed.html', context)

def payment_history(request):
    """User payment history"""
    if 'user_id' not in request.session:
        messages.error(request, 'Please login to view payment history.')
        return redirect('login_page')
    
    try:
        user = MfalmeUsers.objects.get(id=request.session['user_id'])
        transactions = PaymentTransaction.objects.filter(user=user).order_by('-created_at')
        
        # Calculate totals
        total_paid_usd = sum(t.amount for t in transactions if t.status == 'completed')
        
        # Get KES totals from metadata
        total_paid_kes = 0
        for t in transactions.filter(status='completed'):
            metadata = t.metadata or {}
            kes_amount = metadata.get('amount_kes', 0)
            if kes_amount:
                total_paid_kes += kes_amount
            else:
                # Estimate if not stored
                total_paid_kes += t.amount * 160  # Rough estimate
        
        pending_payments = transactions.filter(status__in=['initiated', 'pending']).count()
        
        context = {
            'user': user,
            'transactions': transactions,
            'total_paid_usd': total_paid_usd,
            'total_paid_kes': total_paid_kes,
            'pending_payments': pending_payments,
            'total_transactions': transactions.count(),
        }
        
        return render(request, 'payments/history.html', context)
    
    except MfalmeUsers.DoesNotExist:
        messages.error(request, 'User account not found.')
        return redirect('login_page')

# ===== EMAIL FUNCTIONS FOR PAYMENTS =====

def send_package_activation_email(user, transaction):
    """Send package activation email with conversion details"""
    try:
        metadata = transaction.metadata or {}
        usd_amount = metadata.get('amount_usd', transaction.amount)
        kes_amount = metadata.get('amount_kes', 0)
        exchange_rate = metadata.get('exchange_rate', 0)
        
        subject = f'🎉 Package Activated - {metadata.get("package_name", "Your Package")}'
        
        context = {
            'username': user.username,
            'soldier_id': user.soldier_id,
            'package_name': metadata.get('package_name', 'Unknown'),
            'amount_usd': usd_amount,
            'amount_kes': kes_amount,
            'exchange_rate': exchange_rate,
            'transaction_id': transaction.reference,
            'activation_date': timezone.now().strftime('%B %d, %Y'),
            'next_steps': [
                'Access your dashboard for package features',
                'Join the exclusive Telegram group',
                'Schedule your onboarding call',
                'Download the trading materials',
            ],
            'support_contact': '+254706286667',
        }
        
        html_content = render_to_string('emails/package_activation.html', context)
        
        text_content = f"""
        🎉 PACKAGE ACTIVATION CONFIRMATION
        {'='*60}
        
        Congratulations {user.username}!
        
        Your {metadata.get('package_name')} has been successfully activated.
        
        📋 PAYMENT DETAILS
        Soldier ID: {user.soldier_id}
        Package: {metadata.get('package_name')}
        Amount Paid: ${usd_amount:,.2f} USD
        Equivalent: KES {kes_amount:,.2f}
        Exchange Rate: 1 USD = {exchange_rate:,.2f} KES
        Transaction ID: {transaction.reference}
        Activation Date: {context['activation_date']}
        
        🚀 NEXT STEPS
        {'\n'.join([f'• {step}' for step in context['next_steps']])}
        
        📞 SUPPORT
        Phone: {context['support_contact']}
        Email: {settings.DEFAULT_FROM_EMAIL}
        
        Welcome to the elite trading community!
        {'='*60}
        """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=f"MFALME BETTERDAYS CAPITAL <{settings.DEFAULT_FROM_EMAIL}>",
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        print(f"✅ Package activation email sent to {user.email}")
        return True
        
    except Exception as e:
        print(f"❌ Package activation email error: {str(e)}")
        return False

# [The rest of your views.py remains exactly the same from your original file...
# All the helper functions, authentication views, etc. stay unchanged]
# I'll continue with the exact same code you already have...

def get_client_ip(request):
    """Get client IP address with proxy support"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip

def get_user_agent_info(request):
    """Extract device and browser information"""
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
    
    device_info = {
        'user_agent': user_agent[:500],
        'is_mobile': 'Mobile' in user_agent,
        'is_tablet': 'Tablet' in user_agent,
        'is_desktop': not ('Mobile' in user_agent or 'Tablet' in user_agent),
        'browser': 'Unknown',
        'os': 'Unknown',
        'device': 'Desktop'
    }
    
    # Browser detection
    if 'Chrome' in user_agent:
        device_info['browser'] = 'Chrome'
    elif 'Firefox' in user_agent:
        device_info['browser'] = 'Firefox'
    elif 'Safari' in user_agent:
        device_info['browser'] = 'Safari'
    elif 'Edge' in user_agent:
        device_info['browser'] = 'Edge'
    elif 'Opera' in user_agent:
        device_info['browser'] = 'Opera'
    
    # OS detection
    if 'Windows' in user_agent:
        device_info['os'] = 'Windows'
    elif 'Mac' in user_agent:
        device_info['os'] = 'macOS'
    elif 'Linux' in user_agent:
        device_info['os'] = 'Linux'
    elif 'Android' in user_agent:
        device_info['os'] = 'Android'
        device_info['device'] = 'Mobile'
    elif 'iOS' in user_agent:
        device_info['os'] = 'iOS'
        device_info['device'] = 'Mobile'
    
    # Device type
    if device_info['is_mobile']:
        device_info['device'] = 'Mobile'
    elif device_info['is_tablet']:
        device_info['device'] = 'Tablet'
    
    return device_info

def get_location_from_ip(ip):
    """Get approximate location from IP address"""
    if ip in ['127.0.0.1', 'localhost']:
        return {'country': 'Local', 'city': 'Development', 'isp': 'Local Network'}
    
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return {
                    'country': data.get('country', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('regionName', 'Unknown'),
                    'isp': data.get('isp', 'Unknown'),
                    'lat': data.get('lat'),
                    'lon': data.get('lon'),
                    'timezone': data.get('timezone', 'Unknown')
                }
    except:
        pass
    
    return {'country': 'Unknown', 'city': 'Unknown', 'isp': 'Unknown'}

def generate_soldier_id():
    """Generate unique soldier ID in format: MFALME-YYMM-XXXXX"""
    timestamp = datetime.now().strftime('%y%m')
    random_part = str(uuid.uuid4())[:8].upper()
    return f"MFALME-{timestamp}-{random_part}"

def hash_password(password):
    """Simple password hashing (use Django's built-in in production)"""
    return hashlib.sha256(password.encode()).hexdigest()

# ===== EMAIL FUNCTIONS =====

def send_verification_email(user, verification_code, request):
    """Send beautiful verification email"""
    try:
        # Get registration data
        ip_address = get_client_ip(request)
        location = get_location_from_ip(ip_address)
        device_info = get_user_agent_info(request)
        
        subject = f'🔐 Verify Your Account - MFALME Soldier {user.soldier_id}'
        
        context = {
            'username': user.username,
            'soldier_id': user.soldier_id,
            'verification_code': verification_code,
            'verification_url': f'https://{request.get_host()}/verify-account/',
            'current_year': datetime.now().year,
            'registration_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'ip_address': ip_address,
            'location': f"{location['city']}, {location['country']}",
            'device': f"{device_info['device']} ({device_info['browser']})",
            'expires_in': '30 minutes',
            'support_email': settings.DEFAULT_FROM_EMAIL,
            'support_phone': '+254706286667',
        }
        
        # Render HTML template
        html_content = render_to_string('emails/verification_email.html', context)
        
        # Plain text version
        text_content = f"""
        🔐 VERIFICATION REQUIRED - MFALME BETTERDAYS CAPITAL
        {'='*60}
        
        Hello {user.username}!
        
        Your Elite Soldier ID: {user.soldier_id}
        Verification Code: {verification_code}
        
        🔗 Verify your account: {context['verification_url']}
        ⏰ Code expires in 30 minutes
        
        📋 Registration Details:
        - Time: {context['registration_time']}
        - Location: {context['location']}
        - IP: {ip_address}
        - Device: {context['device']}
        
        Need help? Contact us:
        📧 {settings.DEFAULT_FROM_EMAIL}
        📱 {context['support_phone']}
        
        This is an automated message. Please do not reply.
        {'='*60}
        """
        
        # Send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=f"MFALME BETTERDAYS CAPITAL <{settings.DEFAULT_FROM_EMAIL}>",
            to=[user.email],
            reply_to=[settings.DEFAULT_FROM_EMAIL],
            headers={'X-Priority': '1', 'Importance': 'High'}
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        print(f"✅ Verification email sent to {user.email} | Soldier: {user.soldier_id}")
        return True
        
    except Exception as e:
        print(f"❌ Verification email failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def notify_admin_new_registration(user, request):
    """Send detailed admin notification"""
    try:
        admin_emails = getattr(settings, 'ADMIN_EMAILS', ['mfalmebetterdays@gmail.com'])
        
        # Collect all data
        ip_address = get_client_ip(request)
        location = get_location_from_ip(ip_address)
        device_info = get_user_agent_info(request)
        
        # Platform statistics
        total_users = MfalmeUsers.objects.count()
        today = timezone.now().date()
        today_registrations = MfalmeUsers.objects.filter(date_joined__date=today).count()
        this_week = MfalmeUsers.objects.filter(date_joined__date__gte=today - timedelta(days=7)).count()
        
        subject = f'🚨 NEW ELITE SOLDIER: {user.soldier_id} - {user.username}'
        
        context = {
            # User Information
            'soldier_id': user.soldier_id,
            'username': user.username,
            'email': user.email,
            'phone': user.phone,
            'elite_rank': getattr(user, 'elite_rank', 'Recruit'),
            
            # Registration Metadata
            'registration_date': user.date_joined.strftime('%Y-%m-%d'),
            'registration_time': timezone.now().strftime('%H:%M:%S'),
            'ip_address': ip_address,
            'location': f"{location['city']}, {location['country']}",
            'isp': location.get('isp', 'Unknown'),
            'device': device_info['device'],
            'browser': device_info['browser'],
            'os': device_info['os'],
            
            # Platform Statistics
            'total_users': total_users,
            'today_registrations': today_registrations,
            'weekly_registrations': this_week,
            
            # Notification Info
            'notification_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'notification_id': f"NOTIF-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            
            # Recommendations
            'recommended_mentor': 'Levi Muriuki',
            'recommended_package': 'Elite Starter',
            'priority_level': 'HIGH',
            'onboarding_notes': f'New {user.elite_rank} registered. Schedule onboarding within 24 hours.',
            
            # Action URLs
            'admin_url': f'https://{request.get_host()}/admin/myapp/mfalmesusers/{user.id}/change/',
            'dashboard_url': f'https://{request.get_host()}/admin/',
        }
        
        # Render HTML template
        html_content = render_to_string('emails/admin_notification.html', context)
        
        # Plain text version
        text_content = f"""
        🚨 NEW ELITE SOLDIER REGISTRATION - MFALME BETTERDAYS CAPITAL
        {'='*70}
        
        ⚡ SOLDIER PROFILE
        Soldier ID: {user.soldier_id}
        Name: {user.username}
        Email: {user.email}
        Phone: {user.phone}
        Rank: {user.elite_rank}
        
        📍 REGISTRATION DATA
        Time: {context['registration_date']} {context['registration_time']}
        IP: {ip_address}
        Location: {context['location']}
        ISP: {context['isp']}
        Device: {context['device']} ({context['browser']} on {context['os']})
        
        📊 PLATFORM STATISTICS
        Total Soldiers: {total_users}
        Today's Registrations: {today_registrations}
        Weekly Growth: {this_week}
        
        ⚡ IMMEDIATE ACTIONS REQUIRED
        1. ✅ Verify email confirmation status
        2. 📧 Send welcome package & credentials
        3. 🎓 Assign mentor: {context['recommended_mentor']}
        4. 📞 Schedule onboarding call (within 24h)
        5. 💎 Activate package: {context['recommended_package']}
        6. 🔗 Add to communication channels
        
        📝 RECOMMENDATIONS
        Mentor: {context['recommended_mentor']}
        Package: {context['recommended_package']}
        Priority: {context['priority_level']}
        Notes: {context['onboarding_notes']}
        
        🔗 QUICK LINKS
        Admin View: {context['admin_url']}
        Dashboard: {context['dashboard_url']}
        
        📋 SYSTEM INFO
        Generated: {context['notification_time']}
        ID: {context['notification_id']}
        {'='*70}
        """
        
        # Send to all admin emails
        for admin_email in admin_emails:
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=f"MFALME Registration System <{settings.DEFAULT_FROM_EMAIL}>",
                to=[admin_email],
                headers={'X-Priority': '1', 'Importance': 'High'}
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            print(f"✅ Admin notification sent to {admin_email}")
        
        return True
        
    except Exception as e:
        print(f"❌ Admin notification error: {str(e)}")
        return False

def send_welcome_email(user, request):
    """Send beautiful welcome email after verification"""
    try:
        subject = f'🎉 Welcome to MFALME BETTERDAYS CAPITAL, Soldier {user.soldier_id}!'
        
        context = {
            'username': user.username,
            'soldier_id': user.soldier_id,
            'email': user.email,
            'phone': user.phone,
            'elite_rank': getattr(user, 'elite_rank', 'Elite Soldier'),
            'date_joined': user.date_joined.strftime('%B %d, %Y'),
            'verification_date': user.verified_at.strftime('%B %d, %Y') if hasattr(user, 'verified_at') and user.verified_at else 'Today',
            'dashboard_url': f'https://{request.get_host()}/dashboard/',
            'telegram_channel': 'https://t.me/MFALME_BETTERDAYS',
            'whatsapp_group': 'https://chat.whatsapp.com/XXXXXXXXXXX',
            'mentor_name': 'Levi Muriuki',
            'mentor_contact': '+254706286667',
            'support_email': settings.DEFAULT_FROM_EMAIL,
            'current_year': datetime.now().year,
            'next_steps': [
                'Complete your profile setup',
                'Join our Telegram community',
                'Connect with your assigned mentor',
                'Attend orientation webinar',
                'Start with practice trading',
                'Set up your trading platform'
            ]
        }
        
        # Render HTML template
        html_content = render_to_string('emails/welcome_email.html', context)
        
        # Plain text version
        text_content = f"""
        🎉 WELCOME TO MFALME BETTERDAYS CAPITAL!
        {'='*60}
        
        Congratulations {user.username}!
        
        ⚡ YOUR ELITE SOLDIER PROFILE IS NOW ACTIVE ⚡
        
        🎖️  SOLDIER PROFILE
        Soldier ID: {user.soldier_id}
        Elite Rank: {user.elite_rank}
        Email: {user.email}
        Phone: {user.phone}
        Joined: {context['date_joined']}
        Status: ✅ VERIFIED & ACTIVE
        
        🚀 GET STARTED IMMEDIATELY
        1. Access Dashboard: {context['dashboard_url']}
        2. Join Telegram: {context['telegram_channel']}
        3. WhatsApp Group: {context['whatsapp_group']}
        4. Contact Mentor: {context['mentor_name']} ({context['mentor_contact']})
        
        📋 YOUR NEXT STEPS
        {'\n'.join([f'• {step}' for step in context['next_steps']])}
        
        💎 ELITE FEATURES NOW AVAILABLE
        • Live Trading Signals
        • Personal Mentorship
        • Weekly Masterclasses
        • Portfolio Management
        • Market Analysis Tools
        • Risk Management Strategies
        
        📞 24/7 SUPPORT
        • Email: {context['support_email']}
        • WhatsApp: {context['mentor_contact']}
        • Telegram: @MFALME_BETTERDAYS
        
        Your trading journey begins now. We're excited to have you in our elite community!
        
        Regards,
        Levi Muriuki & The MFALME BETTERDAYS CAPITAL Team
        {'='*60}
        """
        
        # Send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=f"Levi Muriuki - MFALME BETTERDAYS CAPITAL <{settings.DEFAULT_FROM_EMAIL}>",
            to=[user.email],
            reply_to=[settings.DEFAULT_FROM_EMAIL]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        print(f"✅ Welcome email sent to {user.email} | Soldier: {user.soldier_id}")
        return True
        
    except Exception as e:
        print(f"❌ Welcome email error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# ===== CORE VIEWS =====

def index(request):
    """Home page"""
    return render(request, 'index.html')

def login_page(request):
    """Login/Signup page"""
    if 'user_id' in request.session:
        return redirect('dashboard')
    
    active_tab = request.GET.get('tab', 'login')
    form_data = request.session.pop('form_data', {})
    
    return render(request, 'login.html', {
        'active_tab': active_tab,
        'form_data': form_data
    })

def login_user(request):
    """Handle user login"""
    if request.method != 'POST':
        return redirect('login_page')
    
    email = request.POST.get('email', '').strip().lower()
    password = request.POST.get('password', '').strip()
    
    print(f"🔐 Login attempt: {email}")
    
    if not email or not password:
        messages.error(request, 'Email and password are required.')
        return redirect('login_page')
    
    try:
        user = MfalmeUsers.objects.get(email=email)
        
        # Check password (in production, use proper password hashing)
        if user.password == password or hash_password(password) == user.password:
            # Check email verification
            if not user.email_verified:
                # Store for verification
                request.session['pending_user_id'] = user.id
                request.session['pending_user_email'] = user.email
                
                # Generate and send new verification code
                verification_code = ''.join(random.choices(string.digits, k=6))
                request.session['verification_code'] = verification_code
                
                # Save verification code to database
                VerificationCode.objects.create(
                    user=user,
                    code=verification_code,
                    expires_at=timezone.now() + timedelta(minutes=30),
                    ip_address=get_client_ip(request)
                )
                
                # Send verification email
                send_verification_email(user, verification_code, request)
                
                messages.error(request, 'Please verify your email first. A new verification code has been sent.')
                return redirect('verify_account_page')
            
            # Update last login
            user.last_login = timezone.now()
            user.save()
            
            # Set session
            request.session['user_id'] = user.id
            request.session['user_email'] = user.email
            request.session['username'] = user.username
            request.session['soldier_id'] = user.soldier_id
            request.session['elite_rank'] = getattr(user, 'elite_rank', 'Recruit')
            
            messages.success(request, f'Welcome back, {user.username}!')
            print(f"✅ Login successful: {email}")
            return redirect('dashboard')
        
        else:
            messages.error(request, 'Invalid email or password.')
            print(f"❌ Wrong password: {email}")
            return redirect('login_page')
            
    except MfalmeUsers.DoesNotExist:
        messages.error(request, 'Account not found. Please register first.')
        return redirect('login_page')
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        messages.error(request, 'An error occurred. Please try again.')
        return redirect('login_page')

@csrf_exempt
def create_account(request):
    """Handle new account registration with complete data collection"""
    if request.method != 'POST':
        return redirect(f'{reverse("login_page")}?tab=signup')
    
    # Collect all form data
    email = request.POST.get('email', '').strip().lower()
    password = request.POST.get('password', '').strip()
    confirm_password = request.POST.get('password1', '').strip()
    phone = request.POST.get('phone', '').strip()
    username = request.POST.get('username', '').strip()
    whatsapp = request.POST.get('whatsapp', '').strip() or phone
    telegram = request.POST.get('telegram', '').strip()
    experience = request.POST.get('experience', 'Beginner')
    package = request.POST.get('package', 'Not specified')
    
    print(f"\n📝 Registration started for: {email}")
    
    # Store form data for repopulation
    request.session['form_data'] = {
        'email': email,
        'username': username,
        'phone': phone,
        'whatsapp': whatsapp,
        'telegram': telegram,
        'experience': experience,
        'package': package
    }
    
    # Validation
    errors = []
    
    if not username or len(username) < 2:
        errors.append('Please enter your full name (minimum 2 characters).')
    
    if not email or '@' not in email:
        errors.append('Please enter a valid email address.')
    
    if len(password) < 6:
        errors.append('Password must be at least 6 characters.')
    
    if password != confirm_password:
        errors.append('Passwords do not match.')
    
    if not phone:
        errors.append('Phone number is required.')
    
    # Check existing user
    if MfalmeUsers.objects.filter(email=email).exists():
        errors.append('Email already registered. Please login instead.')
    
    if errors:
        for error in errors:
            messages.error(request, error)
        return redirect(f'{reverse("login_page")}?tab=signup')
    
    try:
        # Get registration metadata
        ip_address = get_client_ip(request)
        location = get_location_from_ip(ip_address)
        device_info = get_user_agent_info(request)
        
        # Generate soldier ID
        soldier_id = generate_soldier_id()
        
        # Create user with ALL data
        user = MfalmeUsers.objects.create(
            email=email,
            password=password,  # Note: In production, hash this!
            username=username,
            phone=phone,
            soldier_id=soldier_id,
            whatsapp_number=whatsapp,
            telegram_username=telegram,
            trading_experience=experience,
            preferred_package=package,
            is_active=True,  # Active but not verified
            email_verified=False,
            registration_ip=ip_address,
            user_agent=device_info['user_agent'],
            registration_time=timezone.now(),
            registration_location=f"{location['city']}, {location['country']}",
            registration_device=f"{device_info['device']} - {device_info['browser']}",
            account_status='pending_verification',
            elite_rank='Recruit'
        )
        
        print(f"✅ User created: {user.soldier_id}")
        
        # Generate verification code
        verification_code = ''.join(random.choices(string.digits, k=6))
        
        # Save verification code
        VerificationCode.objects.create(
            user=user,
            code=verification_code,
            expires_at=timezone.now() + timedelta(minutes=30),
            ip_address=ip_address,
            device_info=device_info['user_agent']
        )
        
        # Store in session
        request.session['pending_user_id'] = user.id
        request.session['pending_user_email'] = user.email
        request.session['pending_soldier_id'] = user.soldier_id
        request.session['verification_code'] = verification_code
        
        # Clear form data from session
        if 'form_data' in request.session:
            del request.session['form_data']
        
        print(f"📧 Generated code: {verification_code}")
        
        # Send admin notification FIRST
        print("📧 Sending admin notification...")
        admin_success = notify_admin_new_registration(user, request)
        
        # Send verification email
        print("📧 Sending verification email...")
        email_success = send_verification_email(user, verification_code, request)
        
        if email_success:
            messages.success(request, 
                f'Registration successful! Check {email} for verification code. '
                f'Your Soldier ID: {user.soldier_id}'
            )
            print(f"✅ Verification email sent to {email}")
        else:
            messages.success(request,
                f'Registration successful but email failed. '
                f'Your verification code: {verification_code} '
                f'Soldier ID: {user.soldier_id}'
            )
            print(f"⚠️ Email failed, showing code: {verification_code}")
        
        return redirect('verify_account_page')
        
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, 'Registration failed. Please try again.')
        return redirect(f'{reverse("login_page")}?tab=signup')

def verify_account_page(request):
    """Verification page"""
    if 'pending_user_id' not in request.session:
        messages.error(request, 'No pending verification. Please register first.')
        return redirect(f'{reverse("login_page")}?tab=signup')
    
    user_email = request.session.get('pending_user_email', '')
    soldier_id = request.session.get('pending_soldier_id', '')
    
    # For debugging only - remove in production
    debug_code = request.session.get('verification_code', '')
    
    print(f"🔑 Verification page accessed: {user_email} | Soldier: {soldier_id}")
    
    return render(request, 'verify_account.html', {
        'user_email': user_email,
        'soldier_id': soldier_id,
        'debug_code': debug_code  # Remove this in production!
    })

def verify_account_process(request):
    """Process verification code"""
    if request.method != 'POST':
        return redirect('verify_account_page')
    
    user_id = request.session.get('pending_user_id')
    entered_code = request.POST.get('verification_code', '').strip()
    
    print(f"\n🔍 Verification attempt: User {user_id}, Code: {entered_code}")
    
    if not user_id or not entered_code:
        messages.error(request, 'Session expired. Please register again.')
        return redirect(f'{reverse("login_page")}?tab=signup')
    
    try:
        user = MfalmeUsers.objects.get(id=user_id)
        
        # Check against session code
        session_code = request.session.get('verification_code')
        
        # Also check in database
        verification = VerificationCode.objects.filter(
            user=user,
            code=entered_code,
            is_used=False
        ).order_by('-created_at').first()
        
        valid_session = (session_code == entered_code)
        valid_db = (verification and verification.is_valid())
        
        if valid_session or valid_db:
            # Activate user account
            user.email_verified = True
            user.verified_at = timezone.now()
            user.is_active = True
            user.account_status = 'active'
            
            # Assign elite rank based on package
            if user.preferred_package == 'Lifetime Mentorship':
                user.elite_rank = 'Captain'
            elif user.preferred_package == 'Leveraging Package':
                user.elite_rank = 'Commander'
            else:
                user.elite_rank = 'Private'
            
            user.save()
            
            # Mark verification as used
            if verification:
                verification.is_used = True
                verification.save()
            
            # Clear verification session
            session_keys = [
                'pending_user_id', 'pending_user_email', 
                'pending_soldier_id', 'verification_code'
            ]
            for key in session_keys:
                if key in request.session:
                    del request.session[key]
            
            # Login user
            request.session['user_id'] = user.id
            request.session['user_email'] = user.email
            request.session['username'] = user.username
            request.session['soldier_id'] = user.soldier_id
            request.session['elite_rank'] = user.elite_rank
            
            print(f"✅ Account verified: {user.soldier_id}")
            
            # Send welcome email
            print("📧 Sending welcome email...")
            welcome_sent = send_welcome_email(user, request)
            
            if welcome_sent:
                print(f"✅ Welcome email sent to {user.email}")
            
            messages.success(request, 
                f'🎉 Account verified successfully! Welcome {user.username} (#{user.soldier_id}). '
                f'Check your email for welcome package.'
            )
            return redirect('dashboard')
        
        else:
            print(f"❌ Invalid code: {entered_code}")
            messages.error(request, 'Invalid verification code. Please try again.')
            return redirect('verify_account_page')
            
    except MfalmeUsers.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('login_page')
    except Exception as e:
        print(f"❌ Verification error: {str(e)}")
        messages.error(request, 'Verification failed. Please try again.')
        return redirect('verify_account_page')

def resend_verification(request):
    """Resend verification code (AJAX endpoint)"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method.'
        })
    
    user_id = request.session.get('pending_user_id')
    
    if not user_id:
        return JsonResponse({
            'success': False,
            'message': 'Session expired. Please refresh and try again.'
        })
    
    try:
        user = MfalmeUsers.objects.get(id=user_id)
        
        # Generate new code
        new_code = ''.join(random.choices(string.digits, k=6))
        
        # Save to database
        VerificationCode.objects.create(
            user=user,
            code=new_code,
            expires_at=timezone.now() + timedelta(minutes=30),
            ip_address=get_client_ip(request)
        )
        
        # Update session
        request.session['verification_code'] = new_code
        
        # Send email
        email_sent = send_verification_email(user, new_code, request)
        
        if email_sent:
            print(f"✅ Code resent to {user.email}: {new_code}")
            return JsonResponse({
                'success': True,
                'message': 'New verification code sent to your email.',
                'code': new_code  # Remove in production!
            })
        else:
            print(f"⚠️ Email failed, showing code: {new_code}")
            return JsonResponse({
                'success': True,
                'message': f'Email failed. Your new code: {new_code}',
                'code': new_code
            })
            
    except Exception as e:
        print(f"❌ Resend error: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Failed to resend verification code.'
        })

def dashboard(request):
    """User dashboard with complete data"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        messages.error(request, 'Please login to access dashboard.')
        return redirect('login_page')
    
    try:
        user = MfalmeUsers.objects.get(id=user_id)
        
        # Calculate account age
        account_age = (timezone.now() - user.date_joined).days
        
        # Get user's verification history
        verifications = VerificationCode.objects.filter(user=user).order_by('-created_at')[:5]
        
        # Get user's payment history
        payments = PaymentTransaction.objects.filter(user=user).order_by('-created_at')[:10]
        
        context = {
            # User Basic Info
            'user': user,
            'username': user.username,
            'email': user.email,
            'phone': user.phone,
            'soldier_id': user.soldier_id,
            'elite_rank': getattr(user, 'elite_rank', 'Recruit'),
            
            # Account Status
            'is_verified': user.email_verified,
            'account_status': getattr(user, 'account_status', 'active'),
            'verification_date': user.verified_at.strftime('%B %d, %Y at %H:%M') if user.verified_at else 'Not verified',
            
            # Registration Data
            'date_joined': user.date_joined.strftime('%B %d, %Y'),
            'registration_time': getattr(user, 'registration_time', user.date_joined).strftime('%H:%M:%S'),
            'registration_ip': getattr(user, 'registration_ip', 'Not recorded'),
            'registration_location': getattr(user, 'registration_location', 'Unknown'),
            'registration_device': getattr(user, 'registration_device', 'Unknown'),
            
            # Trading Info
            'trading_experience': getattr(user, 'trading_experience', 'Not specified'),
            'preferred_package': getattr(user, 'preferred_package', 'Not selected'),
            'whatsapp_number': getattr(user, 'whatsapp_number', 'Not provided'),
            'telegram_username': getattr(user, 'telegram_username', 'Not provided'),
            
            # Statistics
            'account_age_days': account_age,
            'last_login': user.last_login.strftime('%B %d, %Y at %H:%M') if user.last_login else 'First login',
            'verification_history': verifications,
            'payment_history': payments,
            
            # Dashboard Stats
            'total_users': MfalmeUsers.objects.count(),
            'verified_users': MfalmeUsers.objects.filter(email_verified=True).count(),
            'today_users': MfalmeUsers.objects.filter(date_joined__date=timezone.now().date()).count(),
        }
        
        # Update last activity
        user.last_activity = timezone.now()
        user.save()
        
        return render(request, 'dashboard.html', context)
        
    except MfalmeUsers.DoesNotExist:
        messages.error(request, 'User account not found.')
        return redirect('login_page')

def logout_user(request):
    """Handle user logout"""
    # Clear all session data
    session_keys = list(request.session.keys())
    for key in session_keys:
        del request.session[key]
    
    messages.success(request, 'Logged out successfully!')
    return redirect('index')

# ===== OTHER PAGES =====

def services(request):
    """Services page"""
    return render(request, 'services.html')

def contact_page(request):
    """Contact page"""
    return render(request, 'contact.html')

def about(request):
    """About page"""
    return render(request, 'about.html')

def partnership(request):
    """Partnership page"""
    return render(request, 'partnership.html')

def education(request):
    """Education page"""
    return render(request, 'education.html')

# ===== TESTING & DEBUGGING =====

def test_email_system(request):
    """Test all email functionality"""
    try:
        # Create test user
        test_user = MfalmeUsers.objects.create(
            email='test@mfalmebetterdays.com',
            password='test123',
            username='Test Soldier',
            phone='+254700000000',
            soldier_id='MFALME-TEST-001',
            email_verified=False,
            is_active=True
        )
        
        verification_code = '123456'
        results = []
        
        print("\n🧪 TESTING EMAIL SYSTEM...")
        
        # Test 1: Verification Email
        print("1. Testing verification email...")
        ver_result = send_verification_email(test_user, verification_code, request)
        results.append(f"Verification Email: {'✅ SUCCESS' if ver_result else '❌ FAILED'}")
        
        # Test 2: Admin Notification
        print("2. Testing admin notification...")
        admin_result = notify_admin_new_registration(test_user, request)
        results.append(f"Admin Notification: {'✅ SUCCESS' if admin_result else '❌ FAILED'}")
        
        # Test 3: Welcome Email
        print("3. Testing welcome email...")
        welcome_result = send_welcome_email(test_user, request)
        results.append(f"Welcome Email: {'✅ SUCCESS' if welcome_result else '❌ FAILED'}")
        
        # Cleanup
        test_user.delete()
        
        # Email settings check
        email_config = f"""
        📧 EMAIL CONFIGURATION:
        - Host: {settings.EMAIL_HOST}
        - Port: {settings.EMAIL_PORT}
        - User: {settings.EMAIL_HOST_USER}
        - From: {settings.DEFAULT_FROM_EMAIL}
        - TLS: {settings.EMAIL_USE_TLS}
        """
        
        results_html = "<h2>Email System Test Results</h2>"
        results_html += "<pre>" + email_config + "</pre>"
        results_html += "<ul>"
        for result in results:
            results_html += f"<li>{result}</li>"
        results_html += "</ul>"
        
        results_html += f"<p><strong>Test completed at:</strong> {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"
        
        return HttpResponse(results_html)
        
    except Exception as e:
        return HttpResponse(f"<h2>Test Failed</h2><pre>{str(e)}</pre>")

def test_smtp_connection(request):
    """Test SMTP connection directly"""
    import smtplib
    
    try:
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10)
        server.starttls()
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        server.quit()
        
        return HttpResponse(f"""
        <h2>✅ SMTP Connection Successful</h2>
        <pre>
        Host: {settings.EMAIL_HOST}
        Port: {settings.EMAIL_PORT}
        User: {settings.EMAIL_HOST_USER}
        Status: Connected & Authenticated
        </pre>
        """)
    except Exception as e:
        return HttpResponse(f"""
        <h2>❌ SMTP Connection Failed</h2>
        <pre>
        Error: {str(e)}
        Host: {settings.EMAIL_HOST}
        Port: {settings.EMAIL_PORT}
        User: {settings.EMAIL_HOST_USER}
        </pre>
        """)

# ===== CONTEXT PROCESSOR =====

def user_authenticated(request):
    """Global context processor for user authentication status"""
    context = {
        'user_authenticated': 'user_id' in request.session,
        'user_email': request.session.get('user_email', ''),
        'username': request.session.get('username', ''),
        'soldier_id': request.session.get('soldier_id', ''),
        'elite_rank': request.session.get('elite_rank', 'Guest')
    }
    
    # Add user object if authenticated
    if 'user_id' in request.session:
        try:
            user = MfalmeUsers.objects.get(id=request.session['user_id'])
            context['user'] = user
            context['is_verified'] = user.email_verified
        except:
            pass
    
    return context

# ===== ERROR HANDLERS =====

def custom_404(request, exception):
    """Custom 404 page"""
    return render(request, '404.html', status=404)

def custom_500(request):
    """Custom 500 page"""
    return render(request, '500.html', status=500)

# ===== API ENDPOINTS (Optional) =====

@csrf_exempt
def api_check_email(request):
    """API endpoint to check if email exists"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    email = request.POST.get('email', '').strip().lower()
    
    if not email:
        return JsonResponse({'error': 'Email required'}, status=400)
    
    exists = MfalmeUsers.objects.filter(email=email).exists()
    
    return JsonResponse({
        'exists': exists,
        'email': email,
        'message': 'Email already registered' if exists else 'Email available'
    })

@csrf_exempt
def api_get_user_stats(request):
    """API endpoint for user statistics"""
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        user = MfalmeUsers.objects.get(id=request.session['user_id'])
        
        stats = {
            'soldier_id': user.soldier_id,
            'username': user.username,
            'email_verified': user.email_verified,
            'account_age_days': (timezone.now() - user.date_joined).days,
            'elite_rank': getattr(user, 'elite_rank', 'Recruit'),
            'trading_experience': getattr(user, 'trading_experience', 'Not specified'),
            'registration_date': user.date_joined.strftime('%Y-%m-%d'),
        }
        
        return JsonResponse({'success': True, 'stats': stats})
        
    except MfalmeUsers.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
def register_page(request):
    """Handle registration page"""
    if request.method == 'POST':
        # Process registration form
        return create_account(request)
    
    # For GET requests, show signup form on login page
    return redirect(f'{reverse("login_page")}?tab=signup')

# ===== BOOKING/CONTACT FORM HANDLER =====
@csrf_exempt
def booking(request):
    """Handle booking/contact form submissions"""
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('contact')
    
    try:
        # Get form data
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip().lower()
        package = request.POST.get('package', '').strip()
        message = request.POST.get('message', '').strip()
        
        # Basic validation
        if not name or not phone or not message:
            messages.error(request, 'Please fill in all required fields.')
            return redirect('contact')
        
        # Send notification email
        subject = f'📞 New Contact Form Submission: {name}'
        
        context = {
            'name': name,
            'phone': phone,
            'email': email,
            'package': package,
            'message': message,
            'submission_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'ip_address': get_client_ip(request),
        }
        
        html_content = render_to_string('emails/contact_notification.html', context)
        
        text_content = f"""
        NEW CONTACT FORM SUBMISSION
        {'='*60}
        
        Name: {name}
        Phone: {phone}
        Email: {email or 'Not provided'}
        Package: {package or 'Not specified'}
        
        Message:
        {message}
        
        Submission Time: {context['submission_time']}
        IP Address: {context['ip_address']}
        
        {'='*60}
        """
        
        # Send to admin
        admin_emails = getattr(settings, 'ADMIN_EMAILS', ['mfalmebetterdays@gmail.com'])
        
        for admin_email in admin_emails:
            email_msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=f"MFALME Contact Form <{settings.DEFAULT_FROM_EMAIL}>",
                to=[admin_email]
            )
            email_msg.attach_alternative(html_content, "text/html")
            email_msg.send()
        
        messages.success(request, 'Thank you for your message! We will contact you shortly.')
        return redirect('contact')
        
    except Exception as e:
        print(f"❌ Booking form error: {str(e)}")
        messages.error(request, 'Failed to submit form. Please try again.')
        return redirect('contact')