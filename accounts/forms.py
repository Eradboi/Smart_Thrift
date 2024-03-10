from django import forms
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.exceptions import ValidationError
from phonenumber_field.formfields import PhoneNumberField
from .models import ProfilePicture,Plan,Transaction,TradingUser,BankAccountNigerian,BankAccountForeign
from .email import send_register_email
User = get_user_model()
import time
class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, min_length=6)
    password2 = forms.CharField(widget=forms.PasswordInput, min_length=6)
    class Meta:
        model = User
        phone = PhoneNumberField()
        fields = ['username', 'email','password1', 'password2','category','phone']
        widgets ={
            'category': forms.RadioSelect,
        }
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password1
    def send_email(self):
        send_register_email(self.cleaned_data['username'],self.cleaned_data['email'],self.cleaned_data['category'])

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        phone = PhoneNumberField()
        fields = ['username', 'email', 'category','phone']
    def clean_username(self):
        new_username = self.cleaned_data['username']
        existing_user = User.objects.exclude(pk=self.instance.pk).filter(username=new_username)
        
        if existing_user.exists():
            raise forms.ValidationError('This username is already in use. Please choose a different one.')
        
        return new_username
class ProfilePictureUpload(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())
    class Meta:
        model = ProfilePicture
        fields = ['user','image']

class UpdateType(forms.ModelForm):
    class Meta:
        model = Plan
        fields =['type']

class PlanForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'e.g Laptop Saving Plan','label':'Plan Name'}))
    class Meta:
        model = Plan
        widgets ={
                'type': forms.Select,
                'duration': forms.Select,
        }
        fields =['name','type','duration','currency']
        labels = {
            'type': 'Deposit Method',
        }

class TransactionForm(forms.ModelForm):
    amount = forms.DecimalField()

    class Meta:
        model = Transaction
        fields =['amount']
class TradingUserForm(forms.ModelForm):
    
    class Meta:
        model = TradingUser
        fields =['trading_password'] 
    
        labels = {
            'trading_password': 'Six Digit Password',
        }


class UserBankNigerian(forms.ModelForm):
    class Meta:
        model = BankAccountNigerian
        fields =['account_no','account_name','bank_code'] 
    
        labels = {
            'account_name': 'Account Name',
            'account_no': 'Account Number',
            'bank_code': 'Bank',
        }

class UserBankUSA(forms.ModelForm):
    
    class Meta:
        model = BankAccountForeign
        fields = ['account_number', 'routing_number', 'swift_code', 'bank_name',
                  'beneficiary_name', 'beneficiary_address', 'beneficiary_country','currency']
        labels = {
            'account_name': 'Account Name',
            'routing_number': 'Routing Number',
            'swift_code': 'Swift Code',
            'bank_name': 'Bank Name',
            'beneficiary_name': 'Beneficiary Name',
            'beneficiary_address': 'Beneficiary Address',
            'beneficiary_country': 'Beneficiary Country',
        }

class UserBankEU(forms.ModelForm):
    
    class Meta:
        model = BankAccountForeign
        fields = ['account_number', 'routing_number', 'swift_code', 'bank_name',
                  'beneficiary_name', 'beneficiary_country', 'postal_code','street_number', 'street_name', 'city','currency']
        labels = {
            'account_name': 'Account Name',
            'routing_number': 'Routing Number',
            'swift_code': 'Swift Code',
            'bank_name': 'Bank Name',
            'beneficiary_name': 'Beneficiary Name',
            'beneficiary_address': 'Beneficiary Address',
            'beneficiary_country': 'Beneficiary Country',
            'postal_code': 'Postal Code',
            'street_number': 'Street Number',
            'street_name': 'Street Name',
            'city': 'City'
        }
    