import hashlib
import base64
import requests
import urllib.parse
from django.conf import settings
from datetime import datetime

def generate_pesapal_signature(params, consumer_secret):
    """Generate Pesapal signature"""
    # Order matters! Follow Pesapal's exact order
    str_to_sign = params.get('pesapal_transaction_type', '')
    str_to_sign += params.get('pesapal_merchant_reference', '')
    str_to_sign += params.get('pesapal_amount', '')
    str_to_sign += params.get('pesapal_currency', '')
    str_to_sign += params.get('pesapal_description', '')
    str_to_sign += params.get('pesapal_type', '')
    str_to_sign += params.get('pesapal_first_name', '')
    str_to_sign += params.get('pesapal_last_name', '')
    str_to_sign += params.get('pesapal_email_address', '')
    str_to_sign += params.get('pesapal_phone_number', '')
    
    # Generate signature
    signature = base64.b64encode(
        hashlib.sha256(
            (str_to_sign + consumer_secret).encode()
        ).digest()
    ).decode()
    
    return signature

def get_pesapal_iframe_url(params, callback_url, consumer_key, consumer_secret):
    """Generate Pesapal iframe URL"""
    signature = generate_pesapal_signature(params, consumer_secret)
    
    # Build the URL
    base_url = settings.PESAPAL_IFRAME_URL
    
    # Add query parameters
    query_params = {
        'pesapal_request_data': urllib.parse.urlencode(params),
        'pesapal_url': callback_url,
        'oauth_callback': callback_url,
        'pesapal_signature_type': 'SHA256',
        'pesapal_signature': signature,
        'pesapal_consumer_key': consumer_key,
    }
    
    iframe_url = f"{base_url}?{urllib.parse.urlencode(query_params)}"
    
    return iframe_url

def query_pesapal_status(merchant_reference, transaction_tracking_id=None):
    """Query payment status from Pesapal"""
    params = {
        'pesapal_merchant_reference': merchant_reference,
        'pesapal_consumer_key': settings.PESAPAL_CONFIG['CONSUMER_KEY'],
    }
    
    if transaction_tracking_id:
        params['pesapal_transaction_tracking_id'] = transaction_tracking_id
    
    # Generate signature
    str_to_sign = params['pesapal_merchant_reference']
    if transaction_tracking_id:
        str_to_sign += params['pesapal_transaction_tracking_id']
    str_to_sign += params['pesapal_consumer_key']
    
    signature = base64.b64encode(
        hashlib.sha256(
            (str_to_sign + settings.PESAPAL_CONFIG['CONSUMER_SECRET']).encode()
        ).digest()
    ).decode()
    
    params['pesapal_signature'] = signature
    
    # Make request
    response = requests.get(settings.PESAPAL_QUERY_URL, params=params)
    return response.text