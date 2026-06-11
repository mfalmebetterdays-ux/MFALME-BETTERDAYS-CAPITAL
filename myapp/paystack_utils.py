# myapp/paystack_utils.py
import requests
import json
import hmac
import hashlib
from decimal import Decimal
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY
PAYSTACK_PUBLIC_KEY = settings.PAYSTACK_PUBLIC_KEY
PAYSTACK_API_URL = 'https://api.paystack.co'

def initialize_paystack_transaction(amount, email, reference, phone=None, metadata=None):
    """
    Initialize a Paystack transaction
    
    Args:
        amount: Amount in KES (smallest currency unit = 1 KES)
        email: Customer email (REQUIRED by Paystack)
        reference: Unique transaction reference
        phone: Customer phone (optional)
        metadata: Additional metadata dict
    
    Returns:
        dict with authorization_url and access_code
    """
    url = f"{PAYSTACK_API_URL}/transaction/initialize"
    
    headers = {
        'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    
    payload = {
        'amount': int(amount * 100),  # Paystack expects amount in cents (1 KES = 100 cents)
        'email': email,  # REQUIRED by Paystack
        'reference': reference,
        'currency': 'KES',
        'callback_url': f"{settings.SITE_URL}/payment/verify/{reference}/",
    }
    
    if phone:
        payload['phone'] = phone
    
    if metadata:
        payload['metadata'] = metadata
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status'):
                logger.info(f"Paystack transaction initialized: {reference}")
                return {
                    'success': True,
                    'authorization_url': data['data']['authorization_url'],
                    'access_code': data['data']['access_code'],
                    'reference': reference,
                }
            else:
                logger.error(f"Paystack init error: {data.get('message')}")
                return {'success': False, 'error': data.get('message')}
        else:
            logger.error(f"Paystack HTTP {response.status_code}: {response.text}")
            return {'success': False, 'error': f'HTTP {response.status_code}'}
            
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Request timeout'}
    except Exception as e:
        logger.error(f"Paystack init exception: {e}")
        return {'success': False, 'error': str(e)}


def verify_paystack_transaction(reference):
    """
    Verify a Paystack transaction status
    
    Args:
        reference: Transaction reference
    
    Returns:
        dict with transaction details
    """
    url = f"{PAYSTACK_API_URL}/transaction/verify/{reference}"
    
    headers = {
        'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status') and data.get('data', {}).get('status') == 'success':
                transaction_data = data['data']
                return {
                    'success': True,
                    'status': 'completed',
                    'amount': transaction_data.get('amount', 0) / 100,  # Convert from cents
                    'currency': transaction_data.get('currency', 'KES'),
                    'reference': reference,
                    'paystack_reference': transaction_data.get('reference'),
                    'paid_at': transaction_data.get('paid_at'),
                    'customer': transaction_data.get('customer', {}),
                }
            else:
                return {
                    'success': False,
                    'status': data.get('data', {}).get('status', 'failed'),
                    'error': data.get('message', 'Verification failed')
                }
        else:
            return {'success': False, 'error': f'HTTP {response.status_code}'}
            
    except Exception as e:
        logger.error(f"Paystack verify exception: {e}")
        return {'success': False, 'error': str(e)}


def initiate_mpesa_payment(amount, email, phone, reference):
    """
    Initiate M-PESA payment via Paystack
    
    Paystack requires phone number for M-PESA
    """
    url = f"{PAYSTACK_API_URL}/charge"
    
    headers = {
        'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    
    # Format phone number for Paystack (requires 254XXXXXXXXX)
    phone = str(phone).strip()
    phone = ''.join(filter(str.isdigit, phone))
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    elif not phone.startswith('254'):
        phone = '254' + phone
    
    payload = {
        'amount': int(amount * 100),
        'email': email,
        'currency': 'KES',
        'reference': reference,
        'mobile_money': {
            'provider': 'mpesa',
            'phone': phone,
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status'):
                return {
                    'success': True,
                    'reference': reference,
                    'message': 'STK Push sent to your phone',
                }
            else:
                return {'success': False, 'error': data.get('message')}
        else:
            return {'success': False, 'error': f'HTTP {response.status_code}'}
            
    except Exception as e:
        logger.error(f"Paystack M-PESA exception: {e}")
        return {'success': False, 'error': str(e)}


def create_paystack_charge(amount, email, reference, card_details=None):
    """
    Create a card charge via Paystack
    """
    url = f"{PAYSTACK_API_URL}/transaction/charge_authorization"
    
    headers = {
        'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    
    payload = {
        'amount': int(amount * 100),
        'email': email,
        'reference': reference,
        'currency': 'KES',
    }
    
    if card_details:
        payload['authorization_code'] = card_details.get('authorization_code')
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        data = response.json()
        
        if data.get('status'):
            return {'success': True, 'data': data.get('data')}
        else:
            return {'success': False, 'error': data.get('message')}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}


def verify_paystack_webhook_signature(request):
    """
    Verify that webhook request came from Paystack
    """
    paystack_signature = request.headers.get('x-paystack-signature')
    
    if not paystack_signature:
        return False
    
    # Read the raw request body
    raw_body = request.body.decode('utf-8')
    
    # Compute HMAC SHA512 signature
    computed_signature = hmac.new(
        PAYSTACK_SECRET_KEY.encode('utf-8'),
        raw_body.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()
    
    return hmac.compare_digest(computed_signature, paystack_signature)


def get_banks():
    """Get list of Nigerian banks (for reference)"""
    url = f"{PAYSTACK_API_URL}/bank"
    
    headers = {
        'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if data.get('status'):
            return {'success': True, 'banks': data.get('data')}
        return {'success': False, 'error': data.get('message')}
    except Exception as e:
        return {'success': False, 'error': str(e)}