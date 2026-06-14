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
        amount: Amount in KES (e.g., 12900 for KES 12,900)
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
    
    # IMPORTANT: Paystack expects amount in the smallest currency unit (cents/kobo)
    # For KES: 1 KES = 100 cents, so multiply by 100
    # Example: KES 12,900 = 1,290,000 cents
    amount_in_cents = int(float(amount) * 100)
    
    print(f"💰 Paystack Init - Original amount: {amount} KES")
    print(f"💰 Paystack Init - Amount in cents: {amount_in_cents}")
    print(f"💰 Paystack Init - Email: {email}")
    print(f"💰 Paystack Init - Reference: {reference}")
    
    payload = {
        'amount': amount_in_cents,  # Send in cents! This is the fix
        'email': email,  # REQUIRED by Paystack
        'reference': reference,
        'currency': 'KES',
        'callback_url': f"{settings.SITE_URL}/paystack/verify/{reference}/",
    }
    
    if phone:
        # Format phone number for Paystack (requires 254XXXXXXXXX)
        formatted_phone = str(phone).strip()
        formatted_phone = ''.join(filter(str.isdigit, formatted_phone))
        if formatted_phone.startswith('0'):
            formatted_phone = '254' + formatted_phone[1:]
        elif formatted_phone.startswith('7') and len(formatted_phone) == 9:
            formatted_phone = '254' + formatted_phone
        elif formatted_phone.startswith('+'):
            formatted_phone = formatted_phone[1:]
        if not formatted_phone.startswith('254'):
            formatted_phone = '254' + formatted_phone
        payload['phone'] = formatted_phone
    
    if metadata:
        payload['metadata'] = metadata
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"📡 Paystack Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status'):
                logger.info(f"✅ Paystack transaction initialized: {reference}")
                print(f"✅ Authorization URL: {data['data']['authorization_url']}")
                return {
                    'success': True,
                    'authorization_url': data['data']['authorization_url'],
                    'access_code': data['data']['access_code'],
                    'reference': reference,
                }
            else:
                error_msg = data.get('message', 'Unknown error')
                logger.error(f"❌ Paystack init error: {error_msg}")
                print(f"❌ Paystack error: {error_msg}")
                print(f"❌ Response data: {data}")
                return {'success': False, 'error': error_msg}
        else:
            error_msg = f'HTTP {response.status_code}'
            logger.error(f"❌ Paystack HTTP error: {error_msg}")
            print(f"❌ Response text: {response.text}")
            return {'success': False, 'error': error_msg}
            
    except requests.exceptions.Timeout:
        logger.error("❌ Paystack request timeout")
        return {'success': False, 'error': 'Request timeout'}
    except Exception as e:
        logger.error(f"❌ Paystack init exception: {e}")
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
    
    print(f"🔍 Verifying Paystack transaction: {reference}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"📡 Verify Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status'):
                transaction_data = data.get('data', {})
                transaction_status = transaction_data.get('status')
                
                print(f"📊 Transaction status: {transaction_status}")
                
                if transaction_status == 'success':
                    # Amount from Paystack is in cents, convert back to KES
                    amount_in_cents = transaction_data.get('amount', 0)
                    amount_in_kes = amount_in_cents / 100
                    
                    return {
                        'success': True,
                        'status': 'completed',
                        'amount': amount_in_kes,
                        'currency': transaction_data.get('currency', 'KES'),
                        'reference': reference,
                        'paystack_reference': transaction_data.get('reference'),
                        'paid_at': transaction_data.get('paid_at'),
                        'customer': transaction_data.get('customer', {}),
                        'channel': transaction_data.get('channel'),
                    }
                else:
                    return {
                        'success': False,
                        'status': transaction_status,
                        'error': f'Payment status: {transaction_status}'
                    }
            else:
                error_msg = data.get('message', 'Verification failed')
                return {
                    'success': False,
                    'status': 'failed',
                    'error': error_msg
                }
        else:
            return {'success': False, 'error': f'HTTP {response.status_code}'}
            
    except Exception as e:
        logger.error(f"❌ Paystack verify exception: {e}")
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
    elif phone.startswith('7') and len(phone) == 9:
        phone = '254' + phone
    elif phone.startswith('+'):
        phone = phone[1:]
    if not phone.startswith('254'):
        phone = '254' + phone
    
    # Convert to cents
    amount_in_cents = int(float(amount) * 100)
    
    print(f"💰 M-PESA Init - Amount: {amount} KES ({amount_in_cents} cents)")
    print(f"📱 M-PESA Phone: {phone}")
    
    payload = {
        'amount': amount_in_cents,
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
        
        print(f"📡 M-PESA Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status'):
                logger.info(f"✅ M-PESA charge initiated: {reference}")
                return {
                    'success': True,
                    'reference': reference,
                    'message': 'STK Push sent to your phone',
                    'authorization_url': data.get('data', {}).get('authorization_url')
                }
            else:
                error_msg = data.get('message', 'M-PESA payment failed')
                logger.error(f"❌ M-PESA error: {error_msg}")
                return {'success': False, 'error': error_msg}
        else:
            return {'success': False, 'error': f'HTTP {response.status_code}'}
            
    except Exception as e:
        logger.error(f"❌ Paystack M-PESA exception: {e}")
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
    
    # Convert to cents
    amount_in_cents = int(float(amount) * 100)
    
    payload = {
        'amount': amount_in_cents,
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
        print("❌ No Paystack signature header")
        return False
    
    # Read the raw request body
    raw_body = request.body.decode('utf-8')
    
    # Compute HMAC SHA512 signature
    computed_signature = hmac.new(
        PAYSTACK_SECRET_KEY.encode('utf-8'),
        raw_body.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()
    
    is_valid = hmac.compare_digest(computed_signature, paystack_signature)
    print(f"🔐 Webhook signature valid: {is_valid}")
    
    return is_valid


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


def list_banks():
    """Alias for get_banks"""
    return get_banks()


def check_paystack_balance():
    """Check Paystack account balance (for debugging)"""
    url = f"{PAYSTACK_API_URL}/balance"
    
    headers = {
        'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if data.get('status'):
            return {'success': True, 'balance': data.get('data')}
        return {'success': False, 'error': data.get('message')}
    except Exception as e:
        return {'success': False, 'error': str(e)}