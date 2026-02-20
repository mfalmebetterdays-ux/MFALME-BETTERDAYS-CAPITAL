# myapp/sasapay_utils.py
import requests
import json
import urllib3
import ssl
from django.conf import settings

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Create a custom session that ignores SSL completely
class UnsafeSession(requests.Session):
    def __init__(self):
        super().__init__()
        self.mount('https://', UnsafeHTTPAdapter())

class UnsafeHTTPAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_version'] = ssl.PROTOCOL_TLS
        kwargs['ssl_context'] = self._create_unsafe_context()
        kwargs['assert_hostname'] = False
        return super().init_poolmanager(*args, **kwargs)
    
    def proxy_manager_for(self, *args, **kwargs):
        kwargs['ssl_context'] = self._create_unsafe_context()
        kwargs['assert_hostname'] = False
        return super().proxy_manager_for(*args, **kwargs)
    
    def _create_unsafe_context(self):
        """Create an SSL context that doesn't verify anything"""
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            ctx.set_ciphers('DEFAULT@SECLEVEL=1')
            return ctx
        except:
            return None

# Create global unsafe session
unsafe_session = UnsafeSession()

# Flag to control mock mode - set to False when SasaPay sandbox is working
USE_MOCK_MODE = True  # Set to False to use real SasaPay API

def get_sasapay_token():
    """Get OAuth token from SasaPay"""
    
    if USE_MOCK_MODE:
        print("🔧 MOCK MODE: Returning mock token")
        return "mock_token_for_development"
    
    # Try multiple API endpoints
    endpoints = [
        f"{settings.SASAPAY_API_URL}/oauth/token",
        "https://sandbox.sasapay.com/api/v1/oauth/token",
        "https://api.sasapay.com/api/v1/oauth/token",
    ]
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Cache-Control': 'no-cache',
    }
    
    payload = {
        'client_id': settings.SASAPAY_CONFIG['CLIENT_ID'],
        'client_secret': settings.SASAPAY_CONFIG['CLIENT_SECRET'],
        'grant_type': 'client_credentials'
    }
    
    # Try each endpoint
    for url in endpoints:
        print(f"Trying SasaPay endpoint: {url}")
        
        try:
            response = unsafe_session.post(
                url,
                json=payload,
                headers=headers,
                timeout=10,
                verify=False,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token')
                if token:
                    print(f"✅ Successfully got token from {url}")
                    return token
        except Exception as e:
            print(f"Failed for {url}: {type(e).__name__}")
    
    # If all methods fail, return None
    print("❌ All SasaPay endpoints failed.")
    return None

def initiate_c2b_payment(phone, amount, reference, description):
    """Initiate C2B payment"""
    
    # Check if we're in mock mode
    if USE_MOCK_MODE:
        print("🔧 MOCK MODE: Simulating C2B payment")
        return {
            'success': True,
            'transaction_id': f"MOCK_{reference}",
            'checkout_id': f"CHECKOUT_{reference}",
            'message': 'MOCK: STK Push sent (development mode)',
            'mock': True
        }
    
    # Real implementation starts here
    token = get_sasapay_token()
    if not token:
        return {
            'success': False, 
            'error': 'Could not authenticate with SasaPay'
        }
    
    url = f"{settings.SASAPAY_API_URL}/c2b"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    
    # Format phone
    phone = str(phone).strip()
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    elif phone.startswith('+'):
        phone = phone[1:]
    elif not phone.startswith('254'):
        phone = '254' + phone
    
    payload = {
        'phone_number': phone,
        'amount': str(int(amount)),
        'reference': reference,
        'description': description[:50],
        'callback_url': settings.SASAPAY_CONFIG['CALLBACK_URL']
    }
    
    try:
        response = unsafe_session.post(
            url, 
            json=payload, 
            headers=headers,
            timeout=30,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'transaction_id': data.get('transaction_id'),
                'checkout_id': data.get('checkout_id'),
                'message': data.get('message', 'STK Push sent'),
                'mock': False
            }
        else:
            return {
                'success': False, 
                'error': f"SasaPay error: {response.status_code} - {response.text}",
                'mock': False
            }
    except Exception as e:
        return {
            'success': False, 
            'error': f"Connection error: {str(e)}",
            'mock': False
        }

def initiate_checkout(amount, reference, description, email, phone=None):
    """Initiate web checkout"""
    
    # Check if we're in mock mode
    if USE_MOCK_MODE:
        print("🔧 MOCK MODE: Simulating checkout")
        return {
            'success': True,
            'checkout_id': f"CHECKOUT_{reference}",
            'checkout_url': f"/payment/success/{reference}/",
            'message': 'MOCK: Checkout initiated (development mode)',
            'mock': True
        }
    
    # Real implementation starts here
    token = get_sasapay_token()
    if not token:
        return {
            'success': False, 
            'error': 'Could not authenticate with SasaPay',
            'mock': False
        }
    
    url = f"{settings.SASAPAY_API_URL}/checkout"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    
    payload = {
        'amount': str(int(amount)),
        'reference': reference,
        'description': description[:50],
        'email': email,
        'callback_url': settings.SASAPAY_CONFIG['CALLBACK_URL'],
        'redirect_url': settings.SASAPAY_CONFIG['CALLBACK_URL']
    }
    
    if phone:
        phone = str(phone).strip()
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif phone.startswith('+'):
            phone = phone[1:]
        elif not phone.startswith('254'):
            phone = '254' + phone
        payload['phone_number'] = phone
    
    try:
        response = unsafe_session.post(
            url, 
            json=payload, 
            headers=headers,
            timeout=30,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            checkout_url = f"{settings.SASAPAY_CHECKOUT_URL}/{data.get('checkout_id')}"
            return {
                'success': True,
                'checkout_id': data.get('checkout_id'),
                'checkout_url': checkout_url,
                'message': data.get('message', 'Checkout initiated'),
                'mock': False
            }
        else:
            return {
                'success': False, 
                'error': f"HTTP {response.status_code} - {response.text}",
                'mock': False
            }
    except Exception as e:
        return {
            'success': False, 
            'error': str(e),
            'mock': False
        }

def query_payment_status(transaction_id):
    """Query payment status"""
    
    if USE_MOCK_MODE:
        return {
            'status': 'COMPLETED',
            'message': 'Mock payment completed',
            'mock': True
        }
    
    # Real implementation
    token = get_sasapay_token()
    if not token:
        return {'status': 'ERROR', 'message': 'Authentication failed'}
    
    url = f"{settings.SASAPAY_API_URL}/transaction/{transaction_id}"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    
    try:
        response = unsafe_session.get(
            url, 
            headers=headers,
            timeout=30,
            verify=False
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {'status': 'ERROR', 'message': f"HTTP {response.status_code}"}
    except Exception as e:
        return {'status': 'ERROR', 'message': str(e)}