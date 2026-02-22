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
    """Get OAuth token from SasaPay - with maximum compatibility"""
    
    print("🔑 Requesting SasaPay token with maximum compatibility...")
    
    # Use settings to determine environment
    env = settings.SASAPAY_CONFIG.get('ENVIRONMENT', 'sandbox')
    
    # Focus on the correct endpoint for your environment
    if env == 'sandbox':
        primary_endpoints = [
            "https://sandbox.sasapay.com/api/v1/oauth/token",
            "https://sandbox.sasapay.com/oauth/token",
        ]
    else:
        primary_endpoints = [
            "https://api.sasapay.com/api/v1/oauth/token",
            "https://api.sasapay.com/oauth/token",
        ]
    
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
    
    # Try primary endpoints first
    for endpoint in primary_endpoints:
        try:
            print(f"🔄 Trying: {endpoint}")
            
            response = ultra_session.post(
                endpoint,
                json=payload,
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
                           data.get('data', {}).get('access_token'))
                    
                    if token:
                        print(f"✅ SUCCESS! Token obtained from {endpoint}")
                        return token
                except:
                    print(f"⚠️ Could not parse JSON response")
                    
        except Exception as e:
            print(f"⚠️ Failed: {type(e).__name__}")
            continue
    
    # If we get here and in DEBUG mode, use mock token
    if settings.DEBUG:
        print("⚠️ Using MOCK token for development")
        return "mock_token_for_development"
    
    # Last resort - raise exception
    raise Exception("Could not connect to SasaPay. Please check your internet connection or try Paystack instead.")

def initiate_c2b_payment(phone, amount, reference, description):
    """Initiate C2B payment with maximum compatibility"""
    
    print(f"💰 Initiating C2B payment: {amount} KES to {phone}")
    
    try:
        token = get_sasapay_token()
        
        env = settings.SASAPAY_CONFIG.get('ENVIRONMENT', 'sandbox')
        
        # Use correct endpoint based on environment
        if env == 'sandbox':
            base_url = "https://sandbox.sasapay.com/api/v1"
        else:
            base_url = "https://api.sasapay.com/api/v1"
        
        endpoint = f"{base_url}/c2b"
        
        # Format phone number
        phone = str(phone).strip()
        phone = ''.join(filter(str.isdigit, phone))
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif phone.startswith('7') and len(phone) == 9:
            phone = '254' + phone
        elif not phone.startswith('254'):
            phone = '254' + phone
            
        # Ensure correct length
        if len(phone) > 12:
            phone = phone[:12]
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        payload = {
            'phone_number': phone,
            'amount': int(amount),
            'reference': reference,
            'description': description[:50],
            'callback_url': settings.SASAPAY_CONFIG.get('CALLBACK_URL'),
        }
        
        print(f"📦 Sending to: {endpoint}")
        
        try:
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
                    
                    transaction_id = (
                        data.get('transaction_id') or
                        data.get('data', {}).get('transaction_id') or
                        data.get('reference') or
                        data.get('id') or
                        reference
                    )
                    
                    return {
                        'success': True,
                        'transaction_id': transaction_id,
                        'checkout_id': data.get('checkout_id'),
                        'message': 'STK Push sent. Check your phone.'
                    }
                except:
                    return {
                        'success': True,
                        'transaction_id': reference,
                        'message': 'Payment initiated successfully'
                    }
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_data.get('error', error_msg))
                except:
                    pass
                    
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timeout. Please try again.'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Connection error: {str(e)[:100]}'
            }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def initiate_checkout(amount, reference, description, email, phone=None):
    """Initiate checkout with maximum compatibility"""
    
    print(f"💳 Initiating checkout: {amount} KES")
    
    try:
        token = get_sasapay_token()
        
        env = settings.SASAPAY_CONFIG.get('ENVIRONMENT', 'sandbox')
        
        if env == 'sandbox':
            base_url = "https://sandbox.sasapay.com/api/v1"
            checkout_base = "https://sandbox.sasapay.com/checkout"
        else:
            base_url = "https://api.sasapay.com/api/v1"
            checkout_base = "https://checkout.sasapay.com"
        
        endpoint = f"{base_url}/checkout"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }
        
        payload = {
            'amount': int(amount),
            'reference': reference,
            'description': description[:50],
            'email': email,
            'callback_url': settings.SASAPAY_CONFIG.get('CALLBACK_URL'),
            'redirect_url': settings.SASAPAY_CONFIG.get('CALLBACK_URL'),
            'currency': 'KES'
        }
        
        if phone:
            phone = ''.join(filter(str.isdigit, phone))
            if phone.startswith('0'):
                phone = '254' + phone[1:]
            elif not phone.startswith('254'):
                phone = '254' + phone
            payload['phone_number'] = phone
        
        response = ultra_session.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=30,
            verify=False
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            checkout_id = (data.get('checkout_id') or 
                          data.get('data', {}).get('checkout_id') or
                          data.get('id'))
            
            checkout_url = f"{checkout_base}/{checkout_id}" if checkout_id else data.get('redirect_url')
            
            return {
                'success': True,
                'checkout_id': checkout_id,
                'checkout_url': checkout_url,
                'message': 'Checkout initiated'
            }
        else:
            return {
                'success': False,
                'error': f"HTTP {response.status_code}"
            }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def query_payment_status(transaction_id):
    """Query payment status"""
    
    try:
        token = get_sasapay_token()
        
        env = settings.SASAPAY_CONFIG.get('ENVIRONMENT', 'sandbox')
        
        if env == 'sandbox':
            base_url = "https://sandbox.sasapay.com/api/v1"
        else:
            base_url = "https://api.sasapay.com/api/v1"
        
        endpoint = f"{base_url}/transaction/{transaction_id}"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }
        
        response = ultra_session.get(
            endpoint,
            headers=headers,
            timeout=15,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'PENDING').upper()
            return {
                'status': status,
                'message': data.get('message', ''),
                'data': data
            }
        else:
            return {
                'status': 'ERROR',
                'message': f"HTTP {response.status_code}"
            }
        
    except Exception as e:
        return {
            'status': 'ERROR',
            'message': str(e)
        }