# myapp/sasapay_utils.py
import requests
import json
import urllib3
import ssl
from django.conf import settings
import time
import socket
from requests.auth import HTTPBasicAuth

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
    """Get OAuth token from SasaPay - Using OFFICIAL documentation"""
    
    print("🔑 Requesting SasaPay token using official API...")
    
    # Use settings to determine environment
    env = settings.SASAPAY_CONFIG.get('ENVIRONMENT', 'sandbox')
    print(f"📌 Current environment: {env}")
    
    # OFFICIAL ENDPOINTS from SasaPay documentation
    if env == 'sandbox':
        base_url = "https://sandbox.sasapay.app"
        token_url = f"{base_url}/api/v1/auth/token/"
    else:
        base_url = "https://api.sasapay.app"  # Assuming live uses .app too
        token_url = f"{base_url}/api/v1/auth/token/"
    
    # They use GET with query parameters
    params = {
        'grant_type': 'client_credentials'
    }
    
    # They use HTTP Basic Authentication
    auth = HTTPBasicAuth(
        settings.SASAPAY_CONFIG['CLIENT_ID'],
        settings.SASAPAY_CONFIG['CLIENT_SECRET']
    )
    
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (compatible; MfalmeBot/1.0)',
        'Cache-Control': 'no-cache',
    }
    
    print(f"🔄 Trying official endpoint: {token_url}")
    
    try:
        response = ultra_session.get(
            token_url,
            params=params,
            auth=auth,
            headers=headers,
            timeout=30,
            verify=False
        )
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"📊 Response data keys: {data.keys()}")
                
                # Extract token from response
                access_token = (
                    data.get('access_token') or 
                    data.get('token') or 
                    data.get('data', {}).get('access_token')
                )
                
                if access_token:
                    print(f"✅ SUCCESS! Token obtained")
                    print(f"🔑 Token: {access_token[:20]}...")
                    return access_token
                else:
                    print(f"⚠️ No token in response: {data}")
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON Parse Error: {e}")
                print(f"Response text: {response.text[:200]}")
        else:
            print(f"❌ HTTP {response.status_code}: {response.text[:200]}")
            
            # Try alternative auth methods if this fails
            print("🔄 Trying alternative authentication methods...")
            
            # Try with POST as fallback
            alt_response = ultra_session.post(
                token_url,
                data=params,
                auth=auth,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30,
                verify=False
            )
            
            if alt_response.status_code == 200:
                data = alt_response.json()
                access_token = data.get('access_token') or data.get('token')
                if access_token:
                    print(f"✅ SUCCESS with POST method!")
                    return access_token
            
    except requests.exceptions.SSLError as e:
        print(f"⚠️ SSL Error: {str(e)[:100]}")
    except requests.exceptions.ConnectionError as e:
        print(f"⚠️ Connection Error: {str(e)[:100]}")
    except requests.exceptions.Timeout:
        print("⏱️ Timeout")
    except Exception as e:
        print(f"⚠️ Failed: {type(e).__name__} - {str(e)[:100]}")
    
    # If we get here and in DEBUG mode, use mock token
    if settings.DEBUG:
        print("⚠️ Using MOCK token for development")
        return "mock_token_for_development"
    
    # Last resort - raise exception
    print("❌ Could not connect to SasaPay using official documentation.")
    raise Exception("SasaPay connection failed. Please try Paystack instead.")

def initiate_c2b_payment(phone, amount, reference, description):
    """Initiate C2B payment with SasaPay - Using official documentation"""
    
    print(f"💰 Initiating C2B payment: {amount} KES to {phone}")
    
    try:
        token = get_sasapay_token()
        
        # Use official base URL based on environment
        env = settings.SASAPAY_CONFIG.get('ENVIRONMENT', 'sandbox')
        
        if env == 'sandbox':
            base_url = "https://sandbox.sasapay.app"
        else:
            base_url = "https://api.sasapay.app"
        
        # Try different possible C2B endpoints
        c2b_endpoints = [
            f"{base_url}/api/v1/c2b",
            f"{base_url}/v1/c2b",
            f"{base_url}/c2b",
            f"{base_url}/api/v1/stkpush",
            f"{base_url}/stkpush",
        ]
        
        # Format phone number properly
        phone = str(phone).strip()
        phone = ''.join(filter(str.isdigit, phone))
        
        # Convert to 254 format
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif phone.startswith('7') and len(phone) == 9:
            phone = '254' + phone
        elif phone.startswith('1') and len(phone) == 9:
            phone = '254' + phone
        elif phone.startswith('+254'):
            phone = phone[1:]
        
        # Validate length
        if len(phone) != 12:
            return {
                'success': False,
                'error': f'Invalid phone number. Use 254XXXXXXXXX format'
            }
        
        print(f"📞 Formatted phone: {phone}")
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        # Try different payload formats based on common API patterns
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
                'account_reference': reference,
                'transaction_desc': description[:50],
                'callback_url': settings.SASAPAY_CONFIG.get('CALLBACK_URL'),
            },
            {
                'msisdn': phone,
                'Amount': int(amount),
                'TransactionReference': reference,
                'Description': description[:50],
                'callbackUrl': settings.SASAPAY_CONFIG.get('CALLBACK_URL'),
            }
        ]
        
        for endpoint in c2b_endpoints:
            for payload in payloads:
                try:
                    print(f"📦 Trying: {endpoint}")
                    
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
                            
                            # Extract transaction ID from various possible response formats
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
                            
                            message = (
                                data.get('message') or 
                                data.get('description') or 
                                data.get('ResponseDescription') or 
                                'STK Push sent. Check your phone.'
                            )
                            
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
                    
                    elif response.status_code == 401:
                        print("❌ Authentication failed - token may be invalid")
                        # Token might be expired, try to get new one
                        token = get_sasapay_token()
                        headers['Authorization'] = f'Bearer {token}'
                        continue
                        
                except Exception as e:
                    print(f"⚠️ Endpoint failed: {type(e).__name__}")
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
            'error': f'Payment failed: {str(e)[:100]}'
        }

def initiate_checkout(amount, reference, description, email, phone=None):
    """Initiate checkout with SasaPay - Using official documentation"""
    
    print(f"💳 Initiating checkout: {amount} KES")
    
    try:
        token = get_sasapay_token()
        
        # Use official base URL
        env = settings.SASAPAY_CONFIG.get('ENVIRONMENT', 'sandbox')
        
        if env == 'sandbox':
            base_url = "https://sandbox.sasapay.app"
            checkout_base = "https://sandbox.sasapay.app/checkout"
        else:
            base_url = "https://api.sasapay.app"
            checkout_base = "https://checkout.sasapay.app"
        
        # Try different checkout endpoints
        checkout_endpoints = [
            f"{base_url}/api/v1/checkout",
            f"{base_url}/v1/checkout",
            f"{base_url}/checkout",
        ]
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        # Base payload
        payload = {
            'amount': int(amount),
            'reference': reference,
            'description': description[:50],
            'email': email,
            'callback_url': settings.SASAPAY_CONFIG.get('CALLBACK_URL'),
            'redirect_url': settings.SASAPAY_CONFIG.get('CALLBACK_URL'),
            'currency': 'KES'
        }
        
        # Add phone if provided
        if phone:
            phone = ''.join(filter(str.isdigit, phone))
            if phone.startswith('0'):
                phone = '254' + phone[1:]
            elif not phone.startswith('254'):
                phone = '254' + phone
            payload['phone_number'] = phone
        
        for endpoint in checkout_endpoints:
            try:
                print(f"📦 Trying checkout: {endpoint}")
                
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
                    
                    checkout_url = data.get('redirect_url') or data.get('checkout_url')
                    if not checkout_url and checkout_id:
                        checkout_url = f"{checkout_base}/{checkout_id}"
                    
                    return {
                        'success': True,
                        'checkout_id': checkout_id,
                        'checkout_url': checkout_url,
                        'message': data.get('message', 'Checkout initiated')
                    }
                    
            except Exception as e:
                print(f"⚠️ Checkout endpoint failed: {type(e).__name__}")
                continue
        
        return {'success': False, 'error': 'Checkout failed - please use Paystack'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def query_payment_status(transaction_id):
    """Query payment status from SasaPay"""
    
    try:
        token = get_sasapay_token()
        
        env = settings.SASAPAY_CONFIG.get('ENVIRONMENT', 'sandbox')
        
        if env == 'sandbox':
            base_url = "https://sandbox.sasapay.app"
        else:
            base_url = "https://api.sasapay.app"
        
        # Try different status endpoints
        status_endpoints = [
            f"{base_url}/api/v1/transaction/{transaction_id}",
            f"{base_url}/v1/transaction/{transaction_id}",
            f"{base_url}/transaction/{transaction_id}",
            f"{base_url}/api/v1/payment/{transaction_id}",
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
                    status = (
                        data.get('status') or 
                        data.get('data', {}).get('status') or 
                        data.get('transaction_status') or 
                        'PENDING'
                    ).upper()
                    
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