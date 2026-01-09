# forms.py
from django import forms
import re

class ContactForm(forms.Form):
    """Contact form with validation"""
    name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Your Full Name',
            'autocomplete': 'name'
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'WhatsApp Number',
            'autocomplete': 'tel'
        })
    )
    
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Email Address (Optional)',
            'autocomplete': 'email'
        })
    )
    
    package = forms.ChoiceField(
        required=True,
        choices=[
            ('', 'Select a Package'),
            ('Market Consultation - $200', 'Market Consultation - $200'),
            ('Lifetime Mentorship - $10,000', 'Lifetime Mentorship - $10,000'),
            ('Leveraging Package - $100,000', 'Leveraging Package - $100,000'),
            ('Partnership Inquiry', 'Partnership Inquiry'),
            ('Other Inquiry', 'Other Inquiry'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    
    message = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-textarea',
            'placeholder': 'Your message...',
            'rows': 4,
            'minlength': 20,
            'maxlength': 500
        })
    )
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        
        # Remove all non-digit characters except + at start
        cleaned_phone = re.sub(r'[^\d\+]', '', phone)
        
        # Basic validation - should have at least 10 digits
        digits = re.sub(r'[^\d]', '', cleaned_phone)
        if len(digits) < 10:
            raise forms.ValidationError('Please enter a valid phone number (at least 10 digits)')
        
        return cleaned_phone
    
    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        if len(message) < 20:
            raise forms.ValidationError('Message must be at least 20 characters long')
        if len(message) > 500:
            raise forms.ValidationError('Message cannot exceed 500 characters')
        return message