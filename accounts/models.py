from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from cloudinary.models import CloudinaryField
import uuid
from django.contrib.auth.hashers import make_password,check_password
from django.core.validators import RegexValidator
from phonenumber_field.modelfields import PhoneNumberField
# Create your models here.
class User(AbstractUser):
    CATEGORY_CHOICES = [
        ("Student", 'Student'),
        ("Employed", 'Employed'),
        ("Unemployed", 'Unemployed'),
    ]

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES,null=False,blank=False,default='TBD')
    phone = PhoneNumberField(null=True, blank=True, unique=True)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)

class Plan(models.Model):
    CATEGORY_CHOICES = [
        ("one month", 'One Month'),
        ("three months", 'Three Months'),
        ("six months", 'Six Months'),
        ("one year", 'One Year'),
        ("three years", 'Three Years'),
    ]
    DEPOSIT_CHOICES=[
       ("optional", 'One Off'),
        ("daily", 'Daily'),
        ("weekly", 'Weekly'),
        ("monthly", 'Monthly'), 
    ]
    CURRENCY_CHOICES=[
       ("NGN", 'Naira'),
        ("USD", 'Dollars'),
        ("GBP", 'British Pounds'),
        ("EUR", 'Euros'), 
    ]
    name = models.CharField(max_length=60)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    type = models.CharField(max_length=20, choices=DEPOSIT_CHOICES,null=False,blank=False,default='optional')
    currency = models.CharField(max_length=20, choices=CURRENCY_CHOICES,null=False,blank=False,default='NGN')
    status = models.BooleanField(default=False)
    duration = models.CharField(max_length=20, choices=CATEGORY_CHOICES,null=False,blank=False,default='three months')
    date_created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['name', 'user']
    def __str__(self):
        return self.name
class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    charge = models.DecimalField(max_digits=10, decimal_places=2,null=False,blank=False,default=0.00)
    date = models.DateTimeField(auto_now_add=True)
    transaction_type = models.CharField(max_length=10, choices=[('debit', 'Withdrawal'), ('credit', 'Deposit')])
    completed= models.BooleanField(default=False)
    def __str__(self):
        return f'{self.user} - {self.transaction_type} - {self.completed} - Amount - {self.amount} -- {self.date}'

class BankAccountNigerian(models.Model):
    BANK_CHOICES = [
        ("044", 'Access Bank'),
        ("058", 'Guaranty Trust Bank'),
        ("232", 'Sterling Bank'),
        ("033", 'Union Bank Nigeria Plc'),
        ("057", 'Zenith Bank'),
        ('063',	'Diamond Bank Plc'),
        ('050',	'Ecobank Nigeria'),
        ('084',	'Enterprise Bank Plc'),
        ('070',	'Fidelity Bank Plc'),
        ('011',	'First Bank of Nigeria Plc'),
        ('214',	'First City Monument Bank'),
        ('030',	'Heritage Banking Company Ltd'),
        ('301',	'Jaiz Bank'),
        ('082',	'Keystone Bank Ltd'),
        ('014',	'Mainstreet Bank Plc'),
        ('076',	'Skye Bank Plc'),
        ('039',	'Stanbic IBTC Plc'),
        ('232',	'Sterling Bank Plc'),
        ('032',	'Union Bank Nigeria Plc'),
        ("215",	'Unity Bank Plc'),
        ('035',	'WEMA Bank Plc'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account_no = models.CharField(max_length=20, unique=True)
    bank_code = models.CharField(max_length=20, choices=BANK_CHOICES,null=False,blank=False,default='058')
    account_name = models.CharField(max_length=265)
    def __str__(self):
        return self.account_no
class BankAccountForeign(models.Model):   
    CURRENCY_CHOICES=[
        ("USD", 'Dollars'),
        ("GBP", 'British Pounds'),
        ("EUR", 'Euros'), 
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=20, unique=True)
    currency = models.CharField(max_length=20, choices=CURRENCY_CHOICES,null=False,blank=False,default='USD')
    routing_number = models.CharField(max_length=20)
    swift_code = models.CharField(max_length=20)
    bank_name = models.CharField(max_length=255)
    beneficiary_name = models.CharField(max_length=255)
    beneficiary_address = models.TextField(blank=True, null=True)
    beneficiary_country = models.CharField(max_length=14)
    postal_code = models.CharField(max_length=8, blank=True, null=True)
    street_number = models.CharField(max_length=14, blank=True, null=True)
    street_name = models.CharField(max_length=256, blank=True, null=True)
    city = models.CharField(max_length=36, blank=True, null=True)
    def __str__(self):
        return self.account_number
    
class AutoPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan_name = models.ForeignKey(Plan, on_delete=models.CASCADE)
    name= models.CharField(max_length=500)
    reference = models.CharField(max_length=1000,blank=True, null=True)
    amount = models.CharField(max_length=1000,blank=True, null=True)
    token = models.IntegerField(blank=True, null=True)
class TradingUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    trading_password = models.CharField(max_length=6, validators=[RegexValidator(r'^\d{6}$', 'Enter a 6-digit number.')])

    def set_trading_password(self, raw_password):
        self.trading_password = make_password(raw_password)
        self.save()

    def check_trading_password(self, raw_password):
        return check_password(raw_password, self.trading_password)
    def __str__(self):
        return f"TradingUser: {self.user}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category= models.CharField(max_length=50,blank=True, null=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('read', 'Read'), ('unread', 'Unread')])
    def __str__(self):
        return f'Message: {self.content} for {self.user}'
    
class ProfilePicture(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = CloudinaryField('image')
    def __str__(self):
        return f'{self.user} just uploaded {self.image} as their profile picture'


