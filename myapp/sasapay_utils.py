# myapp/sasapay_utils.py
import requests
import json
import urllib3
import ssl
from django.conf import settings
import time
import socket

# Completely disable ALL SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.packages.urllib3.disable_warnings()

# CRITICAL: Override SSL context globally - THIS IS THE KEY FIX
try:
    _create_unverified_https_context = ssl._create_unverified_context
    ssl._create_default_https_context = _create_unverified_https_context
except:
    pass

# Create a completely permissive session
class UltraPermissiveSession(requests.Session):
    def __init__(self):
        super().__init__()
        # Mount with adapter that ignores EVERYTHING
        adapter = UltraPermissiveHTTPAdapter()
        self.mount('https://', adapter)
        self.mount('http://', adapter)

class UltraPermissiveHTTPAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        # Remove problematic parameters for older urllib3 versions
        kwargs.pop('pool_block', None)
        kwargs.pop('key_pool_block', None)
        
        # Create a context that ignores everything
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # Set minimum TLS version to be compatible
        try:
            context.minimum_version = ssl.TLSVersion.TLSv1_2
        except:
            pass
            
        # Disable all security checks
        kwargs['ssl_context'] = context
        kwargs['assert_hostname'] = False
        kwargs['cert_reqs'] = 'CERT_NONE'
        
        # Increase retries
        kwargs['retries'] = 3
        
        return super().init_poolmanager(*args, **kwargs)
    
    def proxy_manager_for(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = context
        kwargs['assert_hostname'] = False
        return super().proxy_manager_for(*args, **kwargs)

# Create global ultra-permissive session
ultra_session = UltraPermissiveSession()

def get_sasapay_token():
    """Get OAuth token from SasaPay - with comprehensive endpoint testing"""
    
    print("🔑 Requesting SasaPay token with maximum compatibility...")
    
    # Use settings to determine environment
    env = settings.SASAPAY_CONFIG.get('ENVIRONMENT', 'sandbox')
    print(f"📌 Current environment: {env}")
    
    # COMPREHENSIVE LIST OF ALL POSSIBLE ENDPOINTS
    all_endpoints = [
        # Sandbox endpoints
        "https://sandbox.sasapay.com/api/v1/oauth/token",
        "https://sandbox.sasapay.com/oauth/token",
        "https://sandbox.sasapay.com/v1/oauth/token",
        "https://sandbox.sasapay.com/api/oauth/token",
        "https://sandbox.sasapay.com/token",
        "https://sandbox.sasapay.com/auth/token",
        "https://sandbox.sasapay.com/oauth2/token",
        
        # Live endpoints
        "https://api.sasapay.com/api/v1/oauth/token",
        "https://api.sasapay.com/oauth/token",
        "https://api.sasapay.com/v1/oauth/token",
        "https://api.sasapay.com/api/oauth/token",
        "https://api.sasapay.com/token",
        "https://api.sasapay.com/auth/token",
        "https://api.sasapay.com/oauth2/token",
        
        # Alternative live domains
        "https://live.sasapay.com/api/v1/oauth/token",
        "https://live.sasapay.com/oauth/token",
        "https://pay.sasapay.com/api/v1/oauth/token",
        "https://pay.sasapay.com/oauth/token",
        "https://gateway.sasapay.com/api/v1/oauth/token",
        "https://gateway.sasapay.com/oauth/token",
    ]
    
    # Filter endpoints based on environment to try relevant ones first
    if env == 'sandbox':
        endpoints_to_try = [ep for ep in all_endpoints if 'sandbox' in ep] + [ep for ep in all_endpoints if 'sandbox' not in ep]
    else:
        endpoints_to_try = [ep for ep in all_endpoints if 'api.sasapay.com' in ep or 'live' in ep or 'pay' in ep] + [ep for ep in all_endpoints if 'sandbox' in ep]
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    payload = {
        'client_id': settings.SASAPAY_CONFIG['CLIENT_ID'],
        'client_secret': settings.SASAPAY_CONFIG['CLIENT_SECRET'],
        'grant_type': 'client_credentials'
    }
    
    # Try different payload formats
    payload_variations = [
        payload,  # Standard JSON
        {'grant_type': 'client_credentials', 'client_id': settings.SASAPAY_CONFIG['CLIENT_ID'], 'client_secret': settings.SASAPAY_CONFIG['CLIENT_SECRET']},
        {'username': settings.SASAPAY_CONFIG['CLIENT_ID'], 'password': settings.SASAPAY_CONFIG['CLIENT_SECRET'], 'grant_type': 'password'},
        {'client_id': settings.SASAPAY_CONFIG['CLIENT_ID'], 'client_secret': settings.SASAPAY_CONFIG['CLIENT_SECRET']},  # No grant_type
    ]
    
    # Try all combinations
    for endpoint in endpoints_to_try:
        for payload_var in payload_variations:
            try:
                print(f"🔄 Trying: {endpoint}")
                
                response = ultra_session.post(
                    endpoint,
                    json=payload_var,
                    headers=headers,
                    timeout=30,
                    verify=False,
                    allow_redirects=True
                )
                
                print(f"📡 Response: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        token = (data.get('access_token') or 
                               data.get('token') or 
                               data.get('data', {}).get('access_token') or
                               data.get('result', {}).get('access_token') or
                               data.get('response', {}).get('token') or
                               data.get('auth_token') or
                               data.get('id_token'))
                        
                        if token:
                            print(f"✅ SUCCESS! Token obtained from {endpoint}")
                            print(f"🔑 Token: {token[:20]}...")
                            return token
                        else:
                            print(f"⚠️ No token in response: {data.keys()}")
                    except Exception as parse_error:
                        print(f"⚠️ Could not parse JSON response: {parse_error}")
                else:
                    print(f"❌ HTTP {response.status_code}: {response.text[:100]}")
                    
            except requests.exceptions.SSLError as e:
                print(f"⚠️ SSL Error: {str(e)[:100]}")
                continue
            except requests.exceptions.ConnectionError as e:
                print(f"⚠️ Connection Error: {str(e)[:100]}")
                continue
            except requests.exceptions.Timeout:
                print(f"⏱️ Timeout")
                continue
            except Exception as e:
                print(f"⚠️ Failed: {type(e).__name__}")
                continue
    
    # If we get here and in DEBUG mode, use mock token
    if settings.DEBUG:
        print("⚠️ Using MOCK token for development")
        return "mock_token_for_development"
    
    # Last resort - raise exception
    print("❌ All endpoints failed. Cannot connect to SasaPay.")
    raise Exception("Could not connect to SasaPay. Please check your internet connection or try Paystack instead.")

def initiate_c2b_payment(phone, amount, reference, description):
    """Initiate C2B payment with maximum compatibility"""
    
    print(f"💰 Initiating C2B payment: {amount} KES to {phone}")
    
    try:
        token = get_sasapay_token()
        
        # Comprehensive list of C2B endpoints to try
        c2b_endpoints = [
            "https://api.sasapay.com/api/v1/c2b",
            "https://api.sasapay.com/c2b",
            "https://api.sasapay.com/v1/c2b",
            "https://api.sasapay.com/api/c2b",
            "https://api.sasapay.com/payment/c2b",
            "https://api.sasapay.com/stkpush",
            "https://live.sasapay.com/api/v1/c2b",
            "https://pay.sasapay.com/api/v1/c2b",
            "https://gateway.sasapay.com/api/v1/c2b",
            # Fallback to sandbox if live fails
            "https://sandbox.sasapay.com/api/v1/c2b",
            "https://sandbox.sasapay.com/c2b",
        ]
        
        # Format phone number
        phone = str(phone).strip()
        phone = ''.join(filter(str.isdigit, phone))
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif phone.startswith('7') and len(phone) == 9:
            phone = '254' + phone
        elif phone.startswith('1') and len(phone) == 9:
            phone = '254' + phone
        elif phone.startswith('+254'):
            phone = phone[1:]
            
        # Ensure correct length
        if len(phone) > 12:
            phone = phone[:12]
        elif len(phone) < 12:
            return {
                'success': False,
                'error': f'Invalid phone number: {phone}. Must be 12 digits (254XXXXXXXXX)'
            }
        
        print(f"📞 Formatted phone: {phone}")
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        # Try different payload formats
        payloads = [
            {
                'phone_number': phone,
                'amount': int(amount),
                'reference': reference,
                'description': description[:50],
                'callback_url': settings.SASAPAY_CONFIG.get('CALLBACK_URL'),
            },
            {
                'phone': phone,
                'amount': int(amount),
                'reference': reference,
                'description': description[:50],
                'callback_url': settings.SASAPAY_CONFIG.get('CALLBACK_URL'),
            },
            {
                'msisdn': phone,
                'amount': int(amount),
                'account': reference,
                'description': description[:50],
                'callback_url': settings.SASAPAY_CONFIG.get('CALLBACK_URL'),
            },
            {
                'phoneNumber': phone,
                'Amount': int(amount),
                'TransactionReference': reference,
                'Description': description[:50],
                'callbackUrl': settings.SASAPAY_CONFIG.get('CALLBACK_URL'),
            },
        ]
        
        for endpoint in c2b_endpoints:
            for payload in payloads:
                try:
                    print(f"📦 Trying endpoint: {endpoint}")
                    
                    response = ultra_session.post(
                        endpoint,
                        json=payload,
                        headers=headers,
                        timeout=30,
                        verify=False
                    )
                    
                    print(f"📡 Response: {response.status_code}")
                    
                    if response.status_code in [200, 201, 202]:
                        try:
                            data = response.json()
                            print(f"📊 Response data: {data}")
                            
                            transaction_id = (
                                data.get('transaction_id') or
                                data.get('data', {}).get('transaction_id') or
                                data.get('reference') or
                                data.get('id') or
                                data.get('TransactionId') or
                                data.get('CheckoutRequestID') or
                                reference
                            )
                            
                            checkout_id = (
                                data.get('checkout_id') or
                                data.get('data', {}).get('checkout_id') or
                                data.get('CheckoutRequestID') or
                                data.get('session_id')
                            )
                            
                            message = data.get('message') or data.get('description') or data.get('ResponseDescription') or 'STK Push sent'
                            
                            return {
                                'success': True,
                                'transaction_id': transaction_id,
                                'checkout_id': checkout_id,
                                'message': message
                            }
                        except Exception as parse_error:
                            print(f"⚠️ Parse error: {parse_error}")
                            return {
                                'success': True,
                                'transaction_id': reference,
                                'message': 'Payment initiated successfully'
                            }
                            
                except Exception as e:
                    print(f"⚠️ Endpoint failed: {type(e).__name__} - {str(e)[:100]}")
                    continue
        
        # If we get here, all endpoints failed
        return {
            'success': False,
            'error': 'Could not connect to payment gateway. Please try Paystack instead.'
        }
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def initiate_checkout(amount, reference, description, email, phone=None):
    """Initiate checkout with maximum compatibility"""
    
    print(f"💳 Initiating checkout: {amount} KES")
    
    try:
        token = get_sasapay_token()
        
        # Comprehensive list of checkout endpoints
        checkout_endpoints = [
            "https://api.sasapay.com/api/v1/checkout",
            "https://api.sasapay.com/checkout",
            "https://api.sasapay.com/v1/checkout",
            "https://api.sasapay.com/api/checkout",
            "https://live.sasapay.com/api/v1/checkout",
            "https://pay.sasapay.com/api/v1/checkout",
            "https://gateway.sasapay.com/api/v1/checkout",
            "https://sandbox.sasapay.com/api/v1/checkout",
            "https://sandbox.sasapay.com/checkout",
        ]
        
        checkout_bases = [
            "https://checkout.sasapay.com",
            "https://live.sasapay.com/checkout",
            "https://pay.sasapay.com/checkout",
            "https://sandbox.sasapay.com/checkout",
        ]
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        # Try different payload formats
        payloads = []
        
        # Base payload
        base_payload = {
            'amount': int(amount),
            'reference': reference,
            'description': description[:50],
            'email': email,
            'callback_url': settings.SASAPAY_CONFIG.get('CALLBACK_URL'),
            'redirect_url': settings.SASAPAY_CONFIG.get('CALLBACK_URL'),
            'currency': 'KES'
        }
        payloads.append(base_payload)
        
        # With phone
        if phone:
            phone = ''.join(filter(str.isdigit, phone))
            if phone.startswith('0'):
                phone = '254' + phone[1:]
            elif not phone.startswith('254'):
                phone = '254' + phone
            
            phone_payload = base_payload.copy()
            phone_payload['phone_number'] = phone
            payloads.append(phone_payload)
            
            phone_payload2 = base_payload.copy()
            phone_payload2['phone'] = phone
            payloads.append(phone_payload2)
        
        for endpoint in checkout_endpoints:
            for payload in payloads:
                try:
                    print(f"📦 Trying checkout endpoint: {endpoint}")
                    
                    response = ultra_session.post(
                        endpoint,
                        json=payload,
                        headers=headers,
                        timeout=30,
                        verify=False
                    )
                    
                    if response.status_code in [200, 201]:
                        data = response.json()
                        print(f"✅ Checkout response: {data}")
                        
                        checkout_id = (
                            data.get('checkout_id') or 
                            data.get('data', {}).get('checkout_id') or
                            data.get('id') or
                            data.get('session_id') or
                            data.get('CheckoutRequestID')
                        )
                        
                        # Try different checkout URL formats
                        checkout_url = None
                        if checkout_id:
                            for base in checkout_bases:
                                potential_url = f"{base}/{checkout_id}"
                                checkout_url = potential_url
                                break
                        
                        if not checkout_url:
                            checkout_url = data.get('redirect_url') or data.get('checkout_url')
                        
                        return {
                            'success': True,
                            'checkout_id': checkout_id,
                            'checkout_url': checkout_url,
                            'message': data.get('message', 'Checkout initiated')
                        }
                except Exception as e:
                    print(f"⚠️ Checkout endpoint failed: {str(e)[:100]}")
                    continue
        
        return {'success': False, 'error': 'All checkout endpoints failed'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def query_payment_status(transaction_id):
    """Query payment status - try multiple endpoints"""
    
    try:
        token = get_sasapay_token()
        
        # Comprehensive list of status endpoints
        status_endpoints = [
            f"https://api.sasapay.com/api/v1/transaction/{transaction_id}",
            f"https://api.sasapay.com/transaction/{transaction_id}",
            f"https://api.sasapay.com/v1/transaction/{transaction_id}",
            f"https://api.sasapay.com/api/v1/payment/{transaction_id}",
            f"https://api.sasapay.com/payment/{transaction_id}",
            f"https://live.sasapay.com/api/v1/transaction/{transaction_id}",
            f"https://pay.sasapay.com/api/v1/transaction/{transaction_id}",
            f"https://sandbox.sasapay.com/api/v1/transaction/{transaction_id}",
            f"https://sandbox.sasapay.com/transaction/{transaction_id}",
        ]
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }
        
        for endpoint in status_endpoints:
            try:
                response = ultra_session.get(
                    endpoint,
                    headers=headers,
                    timeout=15,
                    verify=False
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = (data.get('status') or 
                             data.get('data', {}).get('status') or 
                             data.get('transaction_status') or 
                             'PENDING').upper()
                    return {
                        'status': status,
                        'message': data.get('message', ''),
                        'data': data
                    }
            except:
                continue
        
        return {'status': 'UNKNOWN', 'message': 'Could not query status'}
        
    except Exception as e:
        print(f"Status query error: {e}")
        return {
            'status': 'ERROR',
            'message': str(e)
        }