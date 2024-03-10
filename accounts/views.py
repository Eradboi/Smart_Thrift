from django.shortcuts import render
from django.shortcuts import render, get_object_or_404,redirect
from .forms import RegisterForm,UserUpdateForm,ProfilePictureUpload,PlanForm,TradingUserForm,UpdateType,UserBankNigerian,UserBankUSA,UserBankEU
from django.http import HttpResponse,JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import *
from django.db import IntegrityError
from django.contrib.auth import logout,authenticate,login
# Create your views here.
from django.views import View
from django.views.decorators.http import require_http_methods
import time
import environ
import json
from django.shortcuts import render
from xhtml2pdf import pisa
from decimal import Decimal
from django.template.loader import get_template
from django.http import HttpResponse,FileResponse
from io import BytesIO
# Initialise environment variables
env = environ.Env()
environ.Env.read_env()
import requests
from datetime import datetime, timedelta
from django.contrib.auth.views import PasswordResetView
from .utils import send_otp
import pyotp
from rave_python import Rave, RaveExceptions, Misc

# login_view
def login_view(request):
    error = None
    if request.method == "POST":
        form = AuthenticationForm(request, request.POST)
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            send_otp(request, username)
            request.session['username'] = username
            request.session['reset_password'] = False
            request.session['usernone'] = False
            return redirect('otp')
        else:
            error = 'Invalid username or password'
    else:
        form = AuthenticationForm(request)
    return render(request, 'accounts/login.html', { 'form': form, 'error':error})
def otp_view(request):
    error = None
    if 'new' in request.POST:
        username = request.session['username']
        send_otp(request, username)
        error = 'A new OTP has been sent to your email address'
        return render(request, 'accounts/otp.html',{'error':error})
    if request.method == "POST":
        otp = request.POST['1']+request.POST['2']+request.POST['3']+request.POST['4']+request.POST['5']+request.POST['6']
        otp_secret_key = request.session['otp_secret_key']
        otp_valid_date = request.session['otp_valid_date']
        if otp_secret_key and otp_valid_date is not None:
            valid_until = datetime.fromisoformat(otp_valid_date)
            if valid_until > datetime.now():
                totp = pyotp.TOTP(otp_secret_key, interval=600)
                if totp.verify(otp):
                    if request.session['usernone'] == False:
                        username = request.session['username']
                        user = get_object_or_404(User, username=username)
                        login(request, user)
                        request.session['otp_secret_key'] = None
                        request.session['otp_valid_date'] = None
                        return redirect('home')
                    else:
                        request.session['reset_password'] = True
                        request.session['otp_secret_key'] = None
                        request.session['otp_valid_date'] = None
                        return redirect('create_tp') 
                else:
                    error = 'Invalid OTP !'
            else:
                error = 'That One Time Password has expired'
        else:
            error = 'Something went wrong while verifying'
    return render(request, 'accounts/otp.html',{'error':error})


# base/ landing page view
def base(request):
    return render(request, 'accounts/base.html')

# sign up page
def register(request):
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # don't save to the database yet
           
            instance = form.save(commit=False)
            instance.set_password(form.cleaned_data['password1'])
            if form.cleaned_data['password1'] == form.cleaned_data['password2']:
                try:
                    instance.is_active = True
                    instance.save()
                    form.send_email()
                except:
                    user = form.cleaned_data.get('username')
                    User.objects.filter(username=user).delete()
                    messages.info(request, f"Internet Connection Error")
                    return redirect('register')
                user = form.cleaned_data.get('username')
                messages.success(request, f"Account created successfully for {user}")
                return redirect('user-login')
            else: 
                for msg in form.errors:
                    ans = str(form.errors[msg]).split("<li>")[1].split("</li>")[0]
                    messages.error(request, f"{msg}: {ans}")
        else:
            for msg in form.errors:
                ans = str(form.errors[msg]).split("<li>")[1].split("</li>")[0]
                messages.error(request, f"{msg}: {ans}")
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', context={'form': form, "errors":form.errors})

# home page
@login_required
def home(request):
    all_NGN = []
    all_USD =[]
    all_GBP = []
    all_EUR = []
    # ------------------------------------------------------
    now = timezone.now()
    time_to_remove = now - timedelta(hours=24)
    recent_transactions = Transaction.objects.filter(
            completed=True,
            user=request.user,
            date__gte=time_to_remove,
            transaction_type='credit'
    )
    transactions_before = Transaction.objects.filter(
        user=request.user,
        completed=True,
        date__lt=time_to_remove,
        transaction_type='credit'
    )
    # for withdrawals
    recent_withdrawals = Transaction.objects.filter(
            completed=True,
            user=request.user,
            date__gte=time_to_remove,
            transaction_type='debit'
    )
    withdrawals_before = Transaction.objects.filter(
        user=request.user,
        completed=True,
        date__lt=time_to_remove,
        transaction_type='debit'
    )
    withdrawals_before_amounts = [transaction.amount for transaction in withdrawals_before]
    transactions_before_amounts = [transaction.amount for transaction in transactions_before]
    all_deposit = sum(transactions_before_amounts)
    all_withdrawals = sum(withdrawals_before_amounts)
    amounts = [transaction.amount for transaction in recent_transactions]
    amounts_withdrawal = [transaction.amount for transaction in recent_withdrawals]
    recent_deposit = sum(amounts)
    recent_withdrawn = sum(amounts_withdrawal)
    if all_deposit > 0:
        percent_increase = round(((recent_deposit/all_deposit)*100), 2)
    else:
        if recent_deposit>0:
            percent_increase = 100
        else:
            percent_increase = 0

    if all_withdrawals > 0:
        percent_decrease = round(((recent_withdrawn/all_withdrawals)*100), 2)
    else:
        if recent_withdrawn > 0:
            percent_decrease = 100
        else:
            percent_decrease = 0
    # For Naira
    plans_NGN = Plan.objects.filter(user=request.user, currency='NGN')
 
    for x in plans_NGN:
        plan = Plan.objects.get(user=request.user,name=x)
        if plan.balance != None:
            all_NGN.append(plan.balance)
        else:
            all_NGN.append(0)  
    total_NGN = sum(all_NGN)
    # For US Dollars
    plans_USD = Plan.objects.filter(user=request.user, currency='USD')
    for x in plans_USD:
        plan = Plan.objects.get(user=request.user,name=x)
        if plan.balance != None:
            all_USD.append(plan.balance)
        else:
            all_USD.append(0)  
    total_USD = sum(all_USD)
    # For British Pounds
    plans_GBP = Plan.objects.filter(user=request.user, currency='GBP')
    for x in plans_GBP:
        plan = Plan.objects.get(user=request.user,name=x)
        if plan.balance != None:
            all_GBP.append(plan.balance)
        else:
            all_GBP.append(0)  
    total_GBP = sum(all_GBP)
    # For Euros
    plans_EUR = Plan.objects.filter(user=request.user, currency='EUR')
    for x in plans_EUR:
        plan = Plan.objects.get(user=request.user,name=x)
        if plan.balance != None:
            all_EUR.append(plan.balance)
        else:
            all_EUR.append(0)  
    total_EUR = sum(all_EUR)
    return render(request, 'accounts/home.html',{'total_NGN':total_NGN,
                                                 'total_USD':total_USD,
                                                 'total_GBP':total_GBP,
                                                 'total_EUR':total_EUR,'withdrawal_balance':recent_withdrawn,
                'deposit_balance':recent_deposit,'percent_increase':percent_increase,'percent_decrease':percent_decrease})
# notifications
@login_required
def notification(request):
    count = Notification.objects.order_by('-timestamp')
    if 'read' in request.POST:
        id = request.POST['read']
        notif = Notification.objects.get(id=id)
        notif.status = 'read'
        notif.save()
        return HttpResponse('<i style="display: none;"></i>')
    if Notification.objects.filter(user=request.user):
        count = Notification.objects.order_by('-timestamp')
        return render(request, 'accounts/notification.html',{'count':count,})
    else:
        response = 'You Are All Caught Up !!'
        return render(request, 'accounts/notification.html',{'response':response})
    
@login_required
def delete_plan(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    if plan.type != 'optional':
        try:
            autoplan = get_object_or_404(AutoPlan, user=request.user,plan_name=plan)
            deletePlan(request,plan_id)
        except:
            pass 
    content = f'{plan.name} succesfully deleted and all attached transactions have been removed'
    notif = Notification.objects.create(user=request.user, category='Plan Deleted', content=content,status='unread')
    notif.save()
    plan.delete()
    messages.info(request, f"{plan} deleted succesfully")
    return redirect('plans')

@login_required
def delete_transaction(request, pk):
    trans = get_object_or_404(Transaction, id=pk)
    content = f'You cancelled a {trans.transaction_type} transaction: {trans.id} of ${trans.amount}. Plan Name: {trans.plan}'
    notif = Notification.objects.create(user=request.user, category='Transaction Cancelled', content=content,status='unread')
    notif.save()
    trans.delete()
    return redirect('notification')
# Users Profile
@login_required
def profilepage(request):
    plans = Plan.objects.filter(user=request.user)
    return render(request, 'accounts/profile.html',{'plans':plans})
@login_required
def editprofile(request):
    
    if request.method == "POST":
        try:
            form = UserUpdateForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, f"Details updated successfully")
                return redirect('profilepage')  # Redirect to the user's profile page after successful update
            else:
               for msg in form.errors:
                ans = str(form.errors[msg]).split("<li>")[1].split("</li>")[0]
                messages.error(request, f"{msg}: {ans}")
                return redirect('editprofile') 
        except:
            for msg in form.errors:
                ans = str(form.errors[msg]).split("<li>")[1].split("</li>")[0]
                messages.error(request, f"{msg}: {ans}")
            return redirect('editprofile')
    else:
        form = UserUpdateForm(instance=request.user)
        
        picture = ProfilePicture.objects.all()
        if f'{request.user} just uploaded' in str(picture):
            return render(request, 'accounts/password.html', {'form': form, "errors":form.errors, 'picture':picture})
        else:
            return render(request, 'accounts/password.html', {'form': form, "errors":form.errors})

@login_required
def editpicture(request):
    plans = Plan.objects.filter(user=request.user)
    if request.method == "POST":
        image = ProfilePictureUpload(request.POST, request.FILES)
        if image.is_valid(): 
            existing_profile_picture = ProfilePicture.objects.filter(user=request.user).first()
            
            if existing_profile_picture:
                # If a profile picture exists, update the existing record
                existing_profile_picture.image = image.cleaned_data['image']
                existing_profile_picture.save()
                messages.success(request, "Profile picture uploaded succesfully")
                return render(request, 'accounts/profile.html')
            else:
                # If no profile picture exists, create a new record
                profile_picture = image.save(commit=False)
                profile_picture.user = request.user
                profile_picture.save()
                messages.success(request, "Profile picture uploaded succesfully")
                return render(request, 'accounts/profile.html')
        else:
            for msg in image.errors:
                ans = str(image.errors[msg]).split("<li>")[1].split("</li>")[0]
                messages.error(request, f"{msg}: {ans}")
            return redirect('editpicture')
    else:
        image = ProfilePictureUpload(initial={
            'user':request.user
        })
        ctx ={'image':image}
        return render(request, 'accounts/picture.html',ctx)

# change trading password
@login_required
def trading_password(request, plan_id, amount):
    error =None
    word = get_object_or_404(Plan, user=request.user, id=plan_id)
    if TradingUser.objects.filter(user=request.user).exists():
        if request.method == 'POST':
            password = request.POST['7']+request.POST['8']+request.POST['9']+request.POST['10']+request.POST['11']+request.POST['12']
            valid = get_object_or_404(TradingUser, user=request.user)
            is_password_correct = valid.check_trading_password(password)
            if is_password_correct:
                request.session['valid'] = True
                request.session['amount'] = amount
                return redirect('plan_deposit', plan_id)
            else:
                error = 'Invalid Password'
    else:
        error = 'Please create a trading password'
        return redirect('create_tp')
    return render(request, 'accounts/trading.html',{'error':error,'word':word})
# second trading password

@login_required
def create_tp(request):
    error = None
    if request.session['reset_password'] == True:
        if 'trading_password' in request.POST:
            request.session['reset_password'] = False
            form = TradingUserForm(request.POST)
            if form.is_valid():
                existing_user = TradingUser.objects.filter(user=request.user).first()
                if existing_user:
                    existing_user.set_trading_password(form.cleaned_data['trading_password'])
                    messages.info(request, 'Trading Password Set Sucessfully You can now create a plan')
                    return redirect('plans')
                else:
                    plan = TradingUser.objects.create(user=request.user)
                    plan.set_trading_password(form.cleaned_data['trading_password'])
                    messages.info(request, 'Trading Password Set Sucessfully You can now Deposit to Your Plans')
                    return redirect('plans')
            else:
                error = 'Wrong Value Input'
        else:
            form = TradingUserForm()
        return render(request, 'accounts/trading_password.html',{'error':error,'form':form})
    else:
        send_otp(request, request.user) 
        request.session['usernone'] = True
        return redirect('otp') 
# Saving Plans Page
@login_required
def plans(request):
    if Plan.objects.filter(user=request.user).exists():
        plan = Plan.objects.filter(user=request.user)
        return render(request, 'accounts/plans.html',{'plans':plan})
    else:
        error = 'Create New Plan Here'
        redirect('create_plan')
    return render(request, 'accounts/plans.html')
import os
# Account Statement
@login_required
def account_statement(request):
    plans = Plan.objects.filter(user=request.user)
        
    NGN = 0
    USD = 0
    EUR = 0
    GBP = 0
    all_NGN = []
    all_USD =[]
    all_GBP = []
    all_EUR = []
    alls_NGN = []
    alls_USD =[]
    alls_GBP = []
    alls_EUR = []
    for x in plans:
        if x.currency == 'NGN':
            NGN += 1
            if x.balance != None:
                all_NGN.append(x.name)
                alls_NGN.append(x.balance)
        if x.currency == 'USD':
            USD += 1
            if x.balance != None:
                all_USD.append(x.name)
                alls_USD.append(x.balance)
        if x.currency == 'GBP':
            GBP += 1
            if x.balance != None:
                all_GBP.append(x.name)
                alls_GBP.append(x.balance)
        if x.currency == 'EUR':
            EUR += 1
            if x.balance != None:
                all_EUR.append(x.name)
                alls_EUR.append(x.balance)
    all_NGN = json.dumps(all_NGN)
    all_USD = json.dumps(all_USD)
    all_GBP = json.dumps(all_GBP)
    all_EUR = json.dumps(all_EUR)
    trans = Transaction.objects.filter(user=request.user, completed=True).order_by('-date')
    if request.method == 'POST':
        for fname in os.listdir():
            if fname.count(request.user.username):
                os.remove(fname)
        template = get_template('statementofaccount.html')

        # Context data for rendering the template
        context = {
            'name': request.user.username,
            'category': request.user.category,
            'email': request.user.email,
            'all_NGN': sum(alls_NGN),
            'all_USD': sum(alls_USD),
            'all_GBP': sum(alls_GBP),
            'all_EUR': sum(alls_EUR),
            'NGN':NGN,
            'USD':USD,
            'GBP':GBP,
            'EUR':EUR, 
            'trans':trans, 
            'plans':plans     
        }
        html_content = template.render(context)

        # Create a PDF response
        pdf = BytesIO()
        pisa.CreatePDF(html_content, dest=pdf)
        pdf_path = f"{request.user.username}'s account_statement.pdf"
        with open(pdf_path, 'wb') as pdf_file:
            pdf_file.write(pdf.getvalue())
        return FileResponse(open(pdf_path,'rb'), as_attachment=True)
    
    alls_NGN = [float(x) for x in alls_NGN if x != None]
    alls_USD = [float(x) for x in alls_USD if x != None]
    alls_GBP = [float(x) for x in alls_GBP if x != None]
    alls_EUR = [float(x) for x in alls_EUR if x != None]
    alls_NGN = json.dumps(alls_NGN)
    alls_USD = json.dumps(alls_USD)
    alls_GBP = json.dumps(alls_GBP)
    alls_EUR = json.dumps(alls_EUR)

    ADD = NGN + USD + GBP + EUR
    NGN_PERCENT = (NGN/ADD)* 100
    USD_PERCENT = (USD/ADD)* 100
    GBP_PERCENT = (GBP/ADD)* 100
    EUR_PERCENT = (EUR/ADD)* 100
    return render(request, 'accounts/statement.html',{'trans':trans,
                                                      'NGN':NGN,
                                                      'USD':USD,
                                                      'GBP':GBP,
                                                      'EUR':EUR,
                                                      'NGN_PERCENT':NGN_PERCENT,'USD_PERCENT':USD_PERCENT,'GBP_PERCENT':GBP_PERCENT,
                                                       'EUR_PERCENT':EUR_PERCENT,
                                                        'total_NGN':all_NGN,
                                                        'total_USD':all_USD,
                                                        'total_GBP':all_GBP,
                                                        'total_EUR':all_EUR,
                                                         'totals_NGN':alls_NGN,
                                                        'totals_USD':alls_USD,
                                                        'totals_GBP':alls_GBP,
                                                        'totals_EUR':alls_EUR, })    
@login_required
def create_plan(request):
    error =None
    if request.method == 'POST':
        form = PlanForm(request.POST)
        if form.is_valid():
            existing_plan = Plan.objects.filter(user=request.user, name=request.POST['name']).first()
            if existing_plan:
                messages.info(request, f'{existing_plan.name} exists already')
                return redirect('plans')
            else:
                plan = form.save(commit=False)
                plan.user = request.user
                plan.save()
                id = plan.id
                messages.info(request, 'Congratulations! You can now add Funds to your Plan Here')
                return redirect('plan_list', plan_id=id)
        else:
            error = 'Wrong Value Input'
    else:
        form = PlanForm()
    return render(request, 'accounts/plan.html',{'error':error,'form':form})

def get_client_ip(request):
    """
    Get the client's IP address from the request.

    Parameters:
    - request: Django HttpRequest object

    Returns:
    - IP address as a string
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    print(ip)
    return ip

def process_payment(request,plan_id, name,email,amount,phone,updated):
    plans = get_object_or_404(Plan, user=request.user, id=plan_id)
    if plans.type == 'optional':
        try:
            trans = get_object_or_404(Transaction,user=request.user, plan=plans, amount=amount, transaction_type='credit', completed=False)
            content = f'Your attempted deposit: {trans.id} of {trans.amount} into {plans.name} is now being processed by Flutterwave'
            notif = get_object_or_404(Notification,user=request.user, category='Deposit Processing', content=content, status='unread')
        except:
            trans = Transaction.objects.create(user=request.user, plan=plans, amount=amount, transaction_type='credit', completed=False)
            content = f'Your attempted deposit: {trans.id} into {plans.name} is now being processed by Flutterwave'
            notif = Notification.objects.create(user=request.user, category='Deposit Processing', content=content, status='unread')
            trans.save()
            notif.save()
        auth_token= env('FLUTTERWAVE_SECRET_KEY')
        hed = {'Authorization': 'Bearer ' + auth_token}
        data = {
                    "tx_ref":f"{str(trans.id)}_{name}_{plan_id}_C",
                    "amount":amount,
                    "currency":plans.currency,
                    "redirect_url":f"http://localhost:8000/deposit_success/",
                    "payment_options":"card,ussd, mobilemoneyghana",
                    "meta":{
                        "consumer_id":23,
                        "consumer_mac":str(plan_id)
                    },
                    "customer":{
                        "email":email,
                        "phonenumber":phone,
                        "name":name
                    },
                    "customizations":{
                        "title":"Smart Thrift",
                        "description":f"Fund {plans.name} Plan",
                        "logo":"https://res.cloudinary.com/dqihcau09/image/upload/v1705198303/logo_l1kgdq.png"
                    }
                    }
        url = ' https://api.flutterwave.com/v3/payments'
        response = requests.post(url, json=data, headers=hed)
        response=response.json()
        print(response)
        link=response['data']['link']
        return link
    else:
        if plans.duration == 'one month':
                if plans.currency:
                    if plans.type == 'daily':
                        dur = 30
                    if plans.type == 'weekly':
                        dur = 4  
                    if plans.type == 'monthly':
                        dur = 1
        if plans.duration == 'three months':
                if plans.currency:
                    if plans.type == 'daily':
                        dur = 90
                    if plans.type == 'weekly':
                        dur = 12 
                    if plans.type == 'monthly':
                        dur = 3
        if plans.duration == 'six months':
                if plans.currency:
                    if plans.type == 'daily':
                        dur = 180
                    if plans.type == 'weekly':
                        dur = 24  
                    if plans.type == 'monthly':
                        dur = 6
        if plans.duration == 'one year':
                if plans.currency == 'NGN':
                    if plans.type == 'daily':
                        dur = 365
                    if plans.type == 'weekly':
                        dur = 52  
                    if plans.type == 'monthly':
                        dur = 12
        if plans.duration == 'three years':
                if plans.currency:
                    if plans.type == 'daily':
                        dur = 1095
                    if plans.type == 'weekly':
                        dur = 156   
                    if plans.type == 'monthly':
                        dur = 36

        if updated == False: 
            trans = Transaction.objects.create(user=request.user, plan=plans, amount=amount, transaction_type='credit', completed=False)
            content = f'Your attempted recurring deposit: {trans.id} into {plans.name} is now being processed by Flutterwave'
            notif = Notification.objects.create(user=request.user, category='Recurring Deposit Processing', content=content, status='unread')
            trans.save()
            notif.save()
            try:
                allow = None
                autoplan = get_object_or_404(AutoPlan, user=request.user,plan_name=plans)
            except:
                allow = True
            time_to_add = timedelta(hours=720)
            # -----------------------------------------------------------------

            # if a payment plan does not exist we will create one
            if allow:
                print('new')
                url = 'https://api.flutterwave.com/v3/payment-plans'
                auth_token= env('FLUTTERWAVE_SECRET_KEY')
                hed = {'Authorization': 'Bearer ' + auth_token}
                data = {
                    "amount": amount,
                    "name": f"SmartThrift Auto Plan {request.user.username}",
                    "currency": plans.currency,
                    "interval": plans.type,
                    "duration": dur
                }
                response = requests.post(url, headers=hed, json=data)
                if response.status_code == 200:
                    print(response.json())
                    response = response.json()
                    payment_plan = response['data']['id']
                    autoplan = AutoPlan.objects.create(user=request.user, plan_name=plans, token=payment_plan,name=f'SmartThrift Auto Plan for {request.user.username}', reference=f'{str(trans.id)}.{name}.{plan_id}', amount=str(amount))
                    autoplan.save()
                    content = f'Your payment plan for {plans.name} is now active'
                    notif = Notification.objects.create(user=request.user, category='Auto Saving Plan', content=content, status='unread')
                    notif.save()

                else:
                    messages.info(request, f"{response.status_code} - {response.text}")
                    return redirect('plan_list',plan_id)
        elif updated == True:
            autoplan = get_object_or_404(AutoPlan, user=request.user,plan_name=plans)
            print('updated')
            url = f'https://api.flutterwave.com/v3/payment-plans/{autoplan.token}'
            auth_token= env('FLUTTERWAVE_SECRET_KEY')
            hed = {'Authorization': 'Bearer ' + auth_token}
            data = {
                "amount": amount,
                "name": f"SmartThrift Auto Plan {request.user.username}",
                "currency": plans.currency,
                "interval": plans.type,
                "duration": dur
            }
            response = requests.put(url, headers=hed, json=data)
            if response.status_code == 200:
                print(response.json())
                response = response.json()
                payment_plan = response['data']['id']
                content = f'Your payment plan for {plans.name} has been updated succesfully'
                notif = Notification.objects.create(user=request.user, category='Auto Saving Plan', content=content, status='unread')
                notif.save()
                autoplan = AutoPlan.objects.update_or_create(user=request.user, plan_name=plans, token=payment_plan,name=f'SmartThrift Auto Plan for {request.user.username}', defaults={
                    'amount': str(amount),
                })

                messages.info(request, f"{response['status']} - {response['message']}")
                return redirect('plan_list',plan_id)
            else:
                messages.info(request, f"{response.status_code} - {response.text}")
                return redirect('plan_list',plan_id)
        auth_token= env('FLUTTERWAVE_SECRET_KEY')
        hed = {'Authorization': 'Bearer ' + auth_token}
        data = {
                    "tx_ref":f"{str(trans.id)}_{name}_{plan_id}_C",
                    "amount":amount,
                    "currency":plans.currency,
                    "redirect_url":f"http://localhost:8000/deposit_success/",
                    "payment_options":"card",
                    "meta":{
                        "consumer_id":request.user.id,
                        "consumer_mac":str(plan_id)
                    },
                    "customer":{
                        "email":email,
                        "phonenumber":phone,
                        "name":name
                    },
                    "customizations":{
                        "title":"Smart Thrift",
                        "description":f"Supscription for {plans.name} Plan",
                        "logo":"https://res.cloudinary.com/dqihcau09/image/upload/v1705198303/logo_l1kgdq.png"
                    },
                    "payment_plan": payment_plan,
                    }
        url = ' https://api.flutterwave.com/v3/payments'
        response = requests.post(url, json=data, headers=hed)
        response=response.json()
        print(response)
        link=response['data']['link']
        return link
    
def deletePlan(request,plan_id):
    plans = get_object_or_404(Plan, user=request.user, id=plan_id)
    autoplan = get_object_or_404(AutoPlan, user=request.user,plan_name=plans)
    auth_token= env('FLUTTERWAVE_SECRET_KEY')
    hed = {'Authorization': 'Bearer ' + auth_token}
    url=f'https://api.flutterwave.com/v3/payment-plans/{autoplan.token}/cancel'
    response = requests.put(url, headers=hed)
    if response.status_code == 200:
        print(response.json())
        response = response.json()
        autoplan.delete()
        messages.info(request, f"{response['status']} - {response['message']}")
        return redirect('plan_list',plan_id)
    else:
        response = response.json()
        messages.info(request, f"{response['status']} - {response['message']}")
        return redirect('plan_list',plan_id)
@login_required
def bank_accounts(request):
    form_nig = UserBankNigerian()
    form_usa = UserBankUSA()
    form_eu = UserBankEU()
    if 'nigerian' in request.POST:
        print('ok')
        form_nig = UserBankNigerian(request.POST)
        if form_nig.is_valid():
            bank = form_nig.save(commit=False)
            bank.user = request.user
            bank.save()
            messages.info(request, 'Account Number Added Succesfully!')
            return redirect('bank_accounts')
        else:
            print('ok')
            for msg in form_nig.errors:
                ans = str(form_nig.errors[msg]).split("<li>")[1].split("</li>")[0]
                messages.info(request, f"{msg}: {ans}")
                return redirect('bank_accounts')
    if 'usa' in request.POST:
        form_usa = UserBankUSA(request.POST)
        if form_usa.is_valid():
            bank = form_usa.save(commit=False)
            bank.user = request.user
            bank.save()
            messages.info(request, 'Account Number Added Succesfully!')
            return redirect('bank_accounts')
        else:
            for msg in form_usa.errors:
                ans = str(form_usa.errors[msg]).split("<li>")[1].split("</li>")[0]
                messages.info(request, f"{msg}: {ans}")
                return redirect('bank_accounts')
    if 'eu' in request.POST:
        form_eu = UserBankEU(request.POST)
        print('IN')
        if form_eu.is_valid():
            bank = form_eu.save(commit=False)
            bank.user = request.user
            bank.save()
            print('INNER')
            messages.info(request, 'Account Number Added Succesfully!')
            return redirect('bank_accounts')
        else:
            print('ok')
            for msg in form_eu.errors:
                ans = str(form_eu.errors[msg]).split("<li>")[1].split("</li>")[0]
                messages.info(request, f"{msg}: {ans}")
                return redirect('bank_accounts')
    else:
        try:
            account_details_nig = BankAccountNigerian.objects.filter(user=request.user)
            account_details_for = BankAccountForeign.objects.filter(user=request.user)
            print(account_details_for)
            return render(request, 'accounts/bank_accounts.html',{'account_nig':account_details_nig,
                                                         'account_for':account_details_for,
                                                         'form_nig':form_nig,'form_usa':form_usa,'form_eu':form_eu})
        except:
            messages.info(request, 'ERROR in displaying details!')
            return render(request, 'accounts/bank_accounts.html',{'form_nig':form_nig,'form_usa':form_usa,'form_eu':form_eu})
@login_required
def plan_deposit(request, plan_id):
    if 'amount' in request.POST:
        try:
            amount = request.POST['amount']
            if not request.session.get('valid'):
                request.session['updated'] = False
                return redirect('trading_password',plan_id=plan_id,amount=amount)
            else:
                request.session['valid'] = False
                messages.info(request, 'Error In Verifying Trading Password')
                return redirect('plan_list', plan_id)
        except:
            messages.info(request, "You didn't enter any value")
            return redirect('plan_list')
    if 'update_amount' in request.POST:
        try:
            amount = request.POST['update_amount']
            if not request.session.get('valid'):
                request.session['updated'] = True
                return redirect('trading_password',plan_id=plan_id,amount=amount)
            else:
                request.session['valid'] = False
                messages.info(request, 'Error In Verifying Trading Password')
                return redirect('plan_list', plan_id)
        except:
            messages.info(request, "You didn't enter any value")
            return redirect('plan_list')
    else:
        if request.session.get('valid'):
            request.session['valid'] = False 
            amount = request.session.get('amount')
            updated = request.session.get('updated')
            return redirect(str(process_payment(request,plan_id, name=request.user.username,email=request.user.email,amount=amount,phone=request.user.phone.as_e164,updated=updated)))
        else:
            messages.info(request, 'Access Denied')
            return redirect('plan_list', plan_id)  
def deposit_success(request):
    tx_ref=request.GET.get('tx_ref')
    status=request.GET.get('status')
    id=request.GET.get('transaction_id')
    if status == 'successful':
        trans_id, user_and_planid = tx_ref.split('_', 1)
            # Splitting user_and_planid based on the second dot
        user, planid = user_and_planid.split('_', 1)
        planid = planid.split('_')[0]
        trans_id = str(trans_id)
        plans = Plan.objects.get(id=planid,user__username=user)
        trans = Transaction.objects.get(id=trans_id,user__username=user, transaction_type='credit')
        # adding balance for the automatic plans
        auth_token= env('FLUTTERWAVE_SECRET_KEY')
        hed = {'Authorization': 'Bearer ' + auth_token}
        url=f'https://api.flutterwave.com/v3/transactions/{id}/verify'

        while True:
            response = requests.get(url, headers=hed)
            if response.status_code == 200:
                response = response.json()
                if trans.completed == False:
                        if response['data']['tx_ref'] == tx_ref:
                            if plans.balance != None:
                                plans.balance += Decimal(round(response['data']["amount_settled"], 2))
                            else:
                                plans.balance = 0
                                plans.balance += Decimal(round(response['data']["amount_settled"], 2))
                            trans.completed = True
                            trans.amount = response['data']["amount_settled"]
                            trans.charge = response['data']['app_fee']
                            trans.save()
                            plans.save()
                            content = f'Your attempted deposit: {trans.id} of {trans.amount} with {trans.charge} charge into {plans.name} is succesful'
                            notif = Notification.objects.create(user=plans.user, category='Deposit Success', content=content, status='unread')
                            notif.save()
                            messages.info(request, f"{response['data']['amount_settled']} Added to {plans.name} succesfully!")
                            user = get_object_or_404(User, username=user)
                            login(request, user)
                            request.session['reset_password'] = True
                            return redirect('home')
                            
                        else:
                            print('NOT')
                else:
                    messages.info(request, f"This link has expired")
                    return redirect('home') 

                
            else:
                print('TRYING AGAIN')
                continue
    else:
        trans_id, user_and_planid = tx_ref.split('_', 1)
        user, planid = user_and_planid.split('_', 1)
        planid = planid.split('_')[0]
        trans_id = str(trans_id)
        plans = Plan.objects.get(id=planid,user__username=user)
        trans = Transaction.objects.get(id=trans_id,user__username=user)
        user = get_object_or_404(User, username=user)
        login(request, user)
        content = f'Your attempted deposit: {trans.id} of {trans.amount} into {plans.name} is unsuccesful'
        notif = Notification.objects.create(user=plans.user, category='Deposit Success', content=content, status='unread')
        notif.save()
        messages.info(request, f'Attempted deposit unsuccesfully :[')
        return redirect('home')

# dynamic page for each plan
@login_required
def plan_list(request, plan_id):
    plans = get_object_or_404(Plan, user=request.user, id=plan_id)
    """auth_token= env('LIVE_API_KEY')
    hed = {'Authorization': 'Bearer ' + auth_token}
    url= 'https://api.flutterwave.com/v3/verify-ip'
    response = requests.get(url, headers=hed)
    print(response.text)"""
    if 'continue' in request.POST:
        form = UpdateType(request.POST, instance=plans)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.user = request.user
            plan.save()
        plans.date_created = datetime.now()
        plans.status = False
        plans.save()
    try:
        check_debit = f'{request.user.username}_{plan_id}_D'
        print(check_debit)
        check_credit = f'{request.user.username}_{plan_id}_C'
        print(check_credit)
        auth_token= env('FLUTTERWAVE_SECRET_KEY')
        hed = {'Authorization': 'Bearer ' + auth_token}
        url= 'https://api.flutterwave.com/v3/transactions'
        response = requests.get(url, headers=hed)
        all_debit = []
        all_credit = []
        if response.status_code == 200:
            response = response.json()
            print(response)
            for x in response['data']:
                if check_debit in x['tx_ref']:
                    all_debit.append(x['amount_settled'])
                if check_credit in x['tx_ref']:
                    all_credit.append(x['amount_settled'])
        print(all_debit)
        print(all_credit)
        count = len(all_debit)
        plans.balance =round((Decimal(sum(all_credit))-Decimal(sum(all_debit))),2)
        plans.save()

        if plans.type != 'optional':
            autoplan = get_object_or_404(AutoPlan,user=request.user,plan_name=plans)
            #----------------------------------------------------------
            
        else:
           autoplan = None
           count = None    
    except:
        count = None 
        autoplan = None
    form = UpdateType(instance=plans)
    accounts_nig = BankAccountNigerian.objects.filter(user=request.user)
    accounts_usd = BankAccountForeign.objects.filter(user=request.user, currency='USD')
    accounts_gbp = BankAccountForeign.objects.filter(user=request.user, currency='GBP')
    accounts_eur = BankAccountForeign.objects.filter(user=request.user, currency='EUR')
    trans = Transaction.objects.filter(user=request.user, plan=plans, completed=True, transaction_type='credit')
    all_12 = []
    all_24 = []
    all_1week = []
    all_2weeks = []
    all_4weeks = []
    now = timezone.now()
    time_12 = now - timedelta(hours=12)
    time_24 = now - timedelta(hours=24)
    time_1week = now - timedelta(hours=168)
    time_2weeks = now - timedelta(hours=336)
    time_4weeks = now - timedelta(hours=720)
    for x in trans:
        if x.date >= time_12:
            all_12.append(x.amount)
        if time_24 <= x.date and x.date < time_12:
           all_24.append(x.amount)
        if time_1week <= x.date and x.date < time_24:
           all_1week.append(x.amount)
        if time_2weeks <= x.date and x.date < time_1week:
           all_2weeks.append(x.amount) 
        if time_4weeks <= x.date and x.date < time_2weeks:
           all_4weeks.append(x.amount)
    twelvehrs = sum(all_12)
    twentyfourhrs = sum(all_24)
    oneweek = sum(all_1week)
    twoweek = sum(all_2weeks)
    fourweek = sum(all_4weeks)
    if True:
        current_time = datetime.now()
        # time tinz
        original_datetime = datetime(plans.date_created.year, plans.date_created.month, plans.date_created.day, plans.date_created.hour, plans.date_created.minute, plans.date_created.second, plans.date_created.microsecond)
        if plans.duration == 'one month':
            # WORKING ON THIS
            time_to_add = timedelta(seconds=2)
            new_datetime = original_datetime + time_to_add
            if current_time >= new_datetime:
                plans.status = False
                plans.save()
                if 'withdrawal' in request.POST:
                    amount = request.POST['amount']
                    print(amount)
                    if Decimal(amount) > plans.balance:
                        messages.info(request, 'Insufficient Plan Balance Error')
                        return redirect('plan_list', plan_id)
                    continue_saving = 'stop'
                    withdrawal = 'withdrawal'
                    return process_withdrawal(request, plans, plan_id, withdrawal,amount)
        if plans.duration == 'three months':
            time_to_add = timedelta(hours=2160)
            new_datetime = original_datetime + time_to_add
            if current_time >= new_datetime:
                print('HERE')
                plans.status = True
                plans.save()
               
                if 'withdrawal' in request.POST:
                    print('HERE 2')
                    amount = request.POST['amount']
                    if Decimal(amount) > plans.balance:
                        messages.info(request, 'Insufficient Plan Balance Error')
                        return redirect('plan_list', plan_id)
                    continue_saving = 'stop'
                    withdrawal = 'withdrawal'
                    return process_withdrawal(request, plans, plan_id, withdrawal,amount)

        if plans.duration == 'six months':
            time_to_add = timedelta(hours=4320)
            new_datetime = original_datetime + time_to_add
            if current_time >= new_datetime:
                plans.status = True
                plans.save()
              
                if 'withdrawal' in request.POST:
                    amount = request.POST['amount']
                    if Decimal(amount) > plans.balance:
                        messages.info(request, 'Insufficient Plan Balance Error')
                        return redirect('plan_list', plan_id)
                    continue_saving = 'stop'
                    withdrawal = 'withdrawal'
                    return process_withdrawal(request, plans, plan_id,withdrawal,amount)

        if plans.duration == 'one year':
            time_to_add = timedelta(hours=8760)
            new_datetime = original_datetime + time_to_add
            if current_time >= new_datetime:
                plans.status = True
                plans.save() 
                
                if 'withdrawal' in request.POST:
                    amount = request.POST['amount']
                    if Decimal(amount) > plans.balance:
                        messages.info(request, 'Insufficient Plan Balance Error')
                        return redirect('plan_list', plan_id)
                    continue_saving = 'stop'
                    withdrawal = 'withdrawal'
                    return process_withdrawal(request, plans, plan_id,withdrawal,amount)

        if plans.duration == 'three years':
            time_to_add = timedelta(hours=26280)
            new_datetime = original_datetime + time_to_add
            if current_time >= new_datetime:
                plans.status = True
                plans.save()
               
                if 'withdrawal' in request.POST:
                    amount = request.POST['amount']
                    if Decimal(amount) > plans.balance:
                        messages.info(request, 'Insufficient Plan Balance Error')
                        return redirect('plan_list', plan_id)
                    continue_saving = 'stop'
                    withdrawal = 'withdrawal'
                    return process_withdrawal(request, plans, plan_id, withdrawal,amount)

    if 'change' in request.POST:
        print('hello')
        form = UpdateType(request.POST, instance=plans)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.user = request.user
            plan.save()
    trans = Transaction.objects.filter(user=request.user, plan=plans, completed=True).order_by('-date')
    return render(request, 'accounts/plan_list.html',{'plan':plans,'form':form,
                                                      'date':new_datetime,'trans':trans,
                                                      'twelvehrs':twelvehrs,'twentyfourhrs':twentyfourhrs,
                                                      'oneweek':oneweek,'twoweek':twoweek,
                                                      'fourweek':fourweek,
                                                      'accounts_nig':accounts_nig,
                                                      'accounts_usd':accounts_usd,
                                                      'accounts_gbp':accounts_gbp,
                                                      'accounts_eur':accounts_eur,
                                                      'autoplan': autoplan,
                                                      'count':count
                                                      })
# for the withdrawal
def process_withdrawal(request, plans, plan_id, withdrawal,amount):
                print("HELLO")
                if withdrawal == 'withdrawal':
                    try:
                        trans = get_object_or_404(Transaction,user=request.user, plan=plans, amount=amount, transaction_type='debit', completed=False)
                        content = f'Your attempted withdrawal: {trans.id} of {trans.amount} out of {plans.name} is now being processed by Flutterwave'
                        notif = get_object_or_404(Notification,user=request.user, category='Withdrawal Processing', content=content, status='unread')
                    except:
                        trans = Transaction.objects.create(user=request.user, plan=plans, amount=amount, transaction_type='debit', completed=False)
                        content = f'Your attempted withdrawal: {trans.id} into {plans.name} is now being processed by Flutterwave'
                        notif = Notification.objects.create(user=request.user, category='Withdrawal Processing', content=content, status='unread')
                        trans.save()
                        notif.save()
                    print('IN')
                    if plans.balance != None and plans.balance != 0.00 and plans.balance >= Decimal(amount):
                        if plans.currency == 'NGN':
                            bank_account = request.POST.get('all_ngn')
                            accounts_naija = BankAccountNigerian.objects.get(user=request.user, account_no=bank_account)
                            print(accounts_naija)
                            auth_token= env('LIVE_API_KEY')
                            hed = {'Authorization': 'Bearer ' + auth_token}
                            url= 'https://api.flutterwave.com/v3/transfers'
                            payload={
                                'account_bank':accounts_naija.bank_code,
                                'account_number': accounts_naija.account_no,
                                'amount': str(amount),
                                'currency':plans.currency,
                                "reference": f"{str(trans.id)}_{request.user.username}_{plan_id}_D",
                                'narration':f"Withdrawal for {request.user.username}'s {plans.name}",
                                "debit_currency": "NGN"
                            }
                            response = requests.post(url, json=payload, headers=hed)
                            print(response.text)
                            while True:
                                
                                if response.status_code == 200:
                                    plans.balance -= Decimal(amount)
                                    plans.save()
                                    response = response.json()
                                    trans = Transaction.objects.update_or_create(id=trans.id, user=request.user,plan=plans,amount=response['data']['amount'],transaction_type='debit', defaults={ 'charge':response['data']['fee'], 'completed':True})
                                    trans.save()
                                    content = f"Your attempted withdrawal: Withdrawal ID {response['data']['id']} of {trans.amount} Naira with {trans.charge} charge out of {plans.name} to {response['data']['full_name']}'s {response['data']['bank_name']} Account  is succesful"
                                    notif = Notification.objects.create(user=plans.user, category='Withdrawal Success', content=content, status='unread')
                                    notif.save()
                                    messages.info(request, f"Your Transfer has been succesfully processed by Flutterwave. You can track it with the ID in your notifications")
                                    return redirect('plan_list', plan_id)
                                else:
                                    retries = 0
                                    while True:
                                        response = response.json()
                                        retry = response['data']['id']
                                        url= f'https://api.flutterwave.com/v3/transfers/{retry}/retries'
                                        response = requests.post(url, headers=hed)
                                        retries += 1
                                        if response.status_code == 429:
                                            content = f"Your attempted withdrawal: ID {response['data']['id']} is pending"
                                            notif = Notification.objects.create(user=plans.user, category='Withdrawal Pending', content=content, status='unread')
                                            notif.save()
                                            messages.info(request, f'Your Transfer is pending. You can track it with the ID in your notifications')
                                            return redirect('plan_list', plan_id)
                                        if response.status_code == 200 and retries >= 5:
                                            print('RETRYING')
                                            plans.balance -= Decimal(amount)
                                            plans.save()
                                            response = response.json()
                                            trans = Transaction.objects.update_or_create(id=trans.id, user=request.user,plan=plans,amount=response['data']['amount'],transaction_type='debit', defaults={ 'charge':response['data']['fee'], 'completed':True})
                                            trans.save()
                                            content = f"Your attempted withdrawal: ID {response['data']['id']} of {trans.amount} Dollars with {trans.charge} charge out of {plans.name} to {response['data']['full_name']}'s {response['data']['bank_name']} Account  is succesful"
                                            notif = Notification.objects.create(user=plans.user, category='Withdrawal Success', content=content, status='unread')
                                            notif.save()
                                            messages.info(request, 'Your Transfer has been succesfully processed by Flutterwave. You can track it with the ID in your notifications')
                                            return redirect('plan_list', plan_id)
                                        else:
                                            content = f"Your attempted withdrawal: ID {response['data']['id']} is pending"
                                            notif = Notification.objects.create(user=plans.user, category='Withdrawal Pending', content=content, status='unread')
                                            notif.save()
                                            messages.info(request, f'Your Transfer is pending. You can track it with the ID in your notifications')
                                            return redirect('plan_list', plan_id) 

                                    
                        if plans.currency == 'USD':
                            bank_account = request.POST.get('all_usd')
                            accounts_usa = BankAccountForeign.objects.get(user=request.user, account_number=bank_account)
                            print(accounts_usa)
                            auth_token= env('LIVE_API_KEY')
                            hed = {'Authorization': 'Bearer ' + auth_token}
                            url= 'https://api.flutterwave.com/v3/transfers'
                            payload = {
                                "amount": str(amount),
                                "narration": f"Withdrawal for {request.user.username}'s {plans.name}",
                                "currency": "USD",
                                "reference": f"{str(trans.id)}_{request.user.username}_{plan_id}_D",
                                "beneficiary_name": request.user.username,
                                "meta": [
                                {
                                "account_number": accounts_usa.account_number,
                                "routing_number": accounts_usa.routing_number,
                                "swift_code": accounts_usa.swift_code,
                                "bank_name": accounts_usa.bank_name,
                                "beneficiary_name": accounts_usa.beneficiary_name,
                                "beneficiary_address": accounts_usa.beneficiary_address,
                                "beneficiary_country": accounts_usa.beneficiary_country
                                }
                            ]
                            }
                            
                            response = requests.post(url, json=payload, headers=hed)
                            print(response.text)
                            
                            if response.status_code == 200:
                                    plans.balance -= Decimal(amount)
                                    plans.save()
                                    response = response.json()
                                    trans = Transaction.objects.update_or_create(id=trans.id, user=request.user,plan=plans,amount=response['data']['amount'],transaction_type='debit', defaults={ 'charge':response['data']['fee'], 'completed':True})
                                    trans.save()
                                    content = f"Your attempted withdrawal: ID {response['data']['id']} of {trans.amount} Dollars with {trans.charge} charge out of {plans.name} to {response['data']['full_name']}'s {response['data']['bank_name']} Account  is succesful"
                                    notif = Notification.objects.create(user=plans.user, category='Withdrawal Success', content=content, status='unread')
                                    notif.save()
                                    messages.info(request, 'Your Transfer has been succesfully processed by Flutterwave. You can track it with the ID in your notifications')
                                    return redirect('plan_list', plan_id)
                            else:
                                retries = 0
                                while True:
                                    response = response.json()
                                    retry = response['data']['id']
                                    url= f'https://api.flutterwave.com/v3/transfers/{retry}/retries'
                                    response = requests.post(url, headers=hed)
                                    retries += 1
                                    if response.status_code == 429:
                                        content = f"Your attempted withdrawal: ID {response['data']['id']} is pending"
                                        notif = Notification.objects.create(user=plans.user, category='Withdrawal Pending', content=content, status='unread')
                                        notif.save()
                                        messages.info(request, f'Your Transfer is pending. You can track it with the ID in your notifications')
                                        return redirect('plan_list', plan_id)
                                    if response.status_code == 200 and retries >= 5:
                                        print('RETRYING')
                                        plans.balance -= Decimal(amount)
                                        plans.save()
                                        response = response.json()
                                        trans = Transaction.objects.update_or_create(id=trans.id, user=request.user,plan=plans,amount=response['data']['amount'],transaction_type='debit', defaults={ 'charge':response['data']['fee'], 'completed':True})
                                        trans.save()
                                        content = f"Your attempted withdrawal: ID {response['data']['id']} of {trans.amount} Dollars with {trans.charge} charge out of {plans.name} to {response['data']['full_name']}'s {response['data']['bank_name']} Account  is succesful"
                                        notif = Notification.objects.create(user=plans.user, category='Withdrawal Success', content=content, status='unread')
                                        notif.save()
                                        messages.info(request, f'Your Transfer has been succesfully processed by Flutterwave. You can track it with the ID in your notifications')
                                        return redirect('plan_list', plan_id)
                                    else:
                                        content = f"Your attempted withdrawal: ID {response['data']['id']} is pending"
                                        notif = Notification.objects.create(user=plans.user, category='Withdrawal Pending', content=content, status='unread')
                                        notif.save()
                                        messages.info(request, f'Your Transfer is pending. You can track it with the ID in your notifications')
                                        return redirect('plan_list', plan_id) 


                            # ----------------------------------------------------------------------
                        if plans.currency == 'EUR' or plans.currency == 'GBP':
                            bank_account = request.POST.get('all_eu')
                            accounts_eu = BankAccountForeign.objects.get(user=request.user, account_number=bank_account)
                            print(accounts_eu)
                            auth_token= env('LIVE_API_KEY')
                            hed = {'Authorization': 'Bearer ' + auth_token}
                            url= 'https://api.flutterwave.com/v3/transfers'
                            payload = {
                                "amount": str(amount),
                                "narration": f"Withdrawal for {request.user.username}'s {plans.name}",
                                "currency": plans.currency,
                                "reference": f"{str(trans.id)}_{request.user.username}_{plan_id}_D",
                                "beneficiary_name": request.user.username,
                                "meta": [
                                    {
                                    "account_number": accounts_eu.account_number,
                                    "routing_number": accounts_eu.routing_number, 
                                    "swift_code": accounts_eu.swift_code, 
                                    "bank_name": accounts_eu.bank_name,
                                    "beneficiary_name": accounts_eu.beneficiary_name,
                                    "beneficiary_country": accounts_eu.beneficiary_country, 
                                    "postal_code": accounts_eu.postal_code, 
                                    "street_number": accounts_eu.street_number,
                                    "street_name": accounts_eu.street_name,
                                    "city": accounts_eu.city
                                    }
                            ]
                            }
                            
                            response = requests.post(url, json=payload, headers=hed)
                            print(response.text)
                            
                            if response.status_code == 200:
                                    plans.balance -= Decimal(amount)
                                    plans.save()
                                    response = response.json()
                                    Transaction.objects.update_or_create(id=trans.id, user=request.user,plan=plans,amount=response['data']['amount'],transaction_type='debit', defaults={ 'charge':response['data']['fee'], 'completed':True})
                                   
                                    if plans.currency == 'GBP':
                                            content = f"Your attempted withdrawal: ID {response['data']['id']} of {trans.amount} Pounds with {trans.charge} charge out of {plans.name} to {response['data']['full_name']}'s {response['data']['bank_name']} Account  is succesful"
                                    if plans.currency == 'EUR':
                                        content = f"Your attempted withdrawal: ID {response['data']['id']} of {trans.amount} Euros with {trans.charge} charge out of {plans.name} to {response['data']['full_name']}'s {response['data']['bank_name']} Account  is succesful"

                                    notif = Notification.objects.create(user=plans.user, category='Withdrawal Success', content=content, status='unread')
                                    notif.save()
                                    messages.info(request, 'Your Transfer has been succesfully processed by Flutterwave. You can track it with the ID in your notifications')
                                    return redirect('plan_list', plan_id)
                            else:
                                retries = 0
                                while True:
                                    response = response.json()
                                    retry = response['data']['id']
                                    url= f'https://api.flutterwave.com/v3/transfers/{retry}/retries'
                                    response = requests.post(url, headers=hed)
                                    retries += 1
                                    if response.status_code == 429:
                                        content = f"Your attempted withdrawal: ID {response['data']['id']} is pending"
                                        notif = Notification.objects.create(user=plans.user, category='Withdrawal Pending', content=content, status='unread')
                                        notif.save()
                                        messages.info(request, f'Your Transfer is pending, you can check the status of your transaction Transaction Tracking Page with this id --> {retry}')
                                        return redirect('plan_list', plan_id)
                                    if response.status_code == 200 and retries >= 5:
                                        print('RETRYING')
                                        plans.balance -= Decimal(amount)
                                        plans.save()
                                        response = response.json()
                                        trans = Transaction.objects.update_or_create(id=trans.id, user=request.user,plan=plans,amount=response['data']['amount'],transaction_type='debit', defaults={ 'charge':response['data']['fee'], 'completed':True})
                                        trans.save()
                                        if plans.currency == 'GBP':
                                            content = f"Your attempted withdrawal: ID {response['data']['id']} of {trans.amount} Pounds with {trans.charge} charge out of {plans.name} to {response['data']['full_name']}'s {response['data']['bank_name']} Account  is succesful"
                                        if plans.currency == 'EUR':
                                            content = f"Your attempted withdrawal: ID {response['data']['id']} of {trans.amount} Euros with {trans.charge} charge out of {plans.name} to {response['data']['full_name']}'s {response['data']['bank_name']} Account  is succesful"

                                        notif = Notification.objects.create(user=plans.user, category='Withdrawal Success', content=content, status='unread')
                                        notif.save()
                                        messages.info(request, f'Your Transfer has been succesfully processed by Flutterwave. You can track it with the ID in your notifications')
                                        return redirect('plan_list', plan_id)
                                    else:
                                        content = f"Your attempted withdrawal: ID {response['data']['id']} is pending"
                                        notif = Notification.objects.create(user=plans.user, category='Withdrawal Pending', content=content, status='unread')
                                        notif.save()
                                        messages.info(request, f'Your Transfer is pending, you can check the status of your transaction at the Transaction Tracking Page with this id --> {retry}')
                                        return redirect('plan_list', plan_id) 
                    else:
                        messages.info(request, 'Plan Balance Account Error')
                        return redirect('plan_list', plan_id)

# For retrying r checking status of transactions
def check_transactions(request, plan_id):
    plans = get_object_or_404(Plan, user=request.user, id=plan_id)
    if 'withdrawal_id' in request.POST:
        if 'retry' in request.POST:
            if plans.balance != None and plans.balance != 0.00:
                try:
                    retry = request.POST['withdrawal_id']
                    auth_token= env('LIVE_API_KEY')
                    hed = {'Authorization': 'Bearer ' + auth_token}
                    url= f'https://api.flutterwave.com/v3/transfers/{retry}/retries'
                
                    response = requests.post(url, headers=hed)
                    if response.status_code == 200:
                        response = response.json()
                        plans.balance -= response['data']['amount']
                        plans.save()
                        trans = Transaction.objects.create(user=request.user,plan=plans,amount=response['data']['amount'], charge=response['data']['fee'], completed=True,transaction_type='debit')
                        trans.save()
                        content = f"Your attempted withdrawal: {trans.id} of {trans.amount} Dollars with {trans.charge} charge out of {plans.name} to {response['data']['full_name']}'s {response['data']['bank_name']} Account  is succesful"
                        notif = Notification.objects.create(user=plans.user, category='Deposit Success', content=content, status='unread')
                        notif.save()
                        display = 'Your Transfer has been succesfully processed by Flutterwave'
                        return render(request, 'accounts/check_transactions.html',{'display':display})
                    else:
                        try:
                            display = f"Your Transfer is couldn't be processed. You can retry at the Transaction Tracking Page with this --> id {response['data']['id']}"
                            return render(request, 'accounts/check_transactions.html',{'display':display})
                        except:
                            display = 'Your Transfer is being processed by Flutterwave'
                            return render(request, 'accounts/check_transactions.html',{'display':display})
                except:
                    display = 'Input Error'
                    return render(request, 'accounts/check_transactions.html',{'display':display})  
            else:
                display = 'Zero Balance Account Error'
                return render(request, 'accounts/check_transactions.html',{'display':display})
        elif 'status' in request.POST:         
            retry = request.POST['withdrawal_id']
            auth_token= env('LIVE_API_KEY')
            hed = {'Authorization': 'Bearer ' + auth_token}
            url= f'https://api.flutterwave.com/v3/transfers/{retry}'
            
            response = requests.get(url, headers=hed)  
            if response.status_code == 200:
                response = response.json()
                display = f"Your Transfer status is {response['status']} -- {response['message']}: Amount {response['data']['amount']}"
                return render(request, 'accounts/check_transactions.html',{'display':display})
            else:
                display = 'Input Error'
                return render(request, 'accounts/check_transactions.html',{'display':display})
    elif 'tx_ref' in request.POST:
        if 'witdrawal' in request.POST:
            tx_ref = request.POST['deposit_id']
            tx_ref = f'{tx_ref}_{request.user.username}_{plan_id}_D'
            print(tx_ref)
            auth_token= env('FLUTTERWAVE_SECRET_KEY')
            hed = {'Authorization': 'Bearer ' + auth_token}
            url= 'https://api.flutterwave.com/v3/transactions'
            payload = {'tx_ref':tx_ref}
            response = requests.get(url, json=payload, headers=hed)
            print(response.text)
            if response.status_code == 200:
                response = response.json()
                display = None
                for x in response['data']:
                    print('IN')
                    if x['tx_ref'] == tx_ref:
                        print('Here')
                        display = f"Your Transfer status is {response['status']} -- {response['message']}: Amount {response['data']['amount']}"
                        break
                    else:
                        messages.info(request, f"ERROR: {response['status']} -- {response['message']}")
                        return redirect('check_transactions')
                return render(request, 'accounts/check_transactions.html',{'display':display})
            else:
                response = response.json()
                messages.info(request, f"ERROR: {response['status']} -- {response['message']}")
                return redirect('check_transactions')
        if 'deposit' in request.POST:
            tx_ref = request.POST['deposit_id']
            tx_ref = f'{tx_ref}_{request.user.username}_{plan_id}_C'
            print(tx_ref)
            auth_token= env('FLUTTERWAVE_SECRET_KEY')
            hed = {'Authorization': 'Bearer ' + auth_token}
            url= 'https://api.flutterwave.com/v3/transactions'
            payload = {'tx_ref':tx_ref}
            response = requests.get(url, json=payload, headers=hed)
            print(response.text)
            if response.status_code == 200:
                response = response.json()
                display = None
                for x in response['data']:
                    print('IN')
                    if x['tx_ref'] == tx_ref:
                        print('Here')
                        display = f"Your Transfer status is {response['status']} -- {response['message']}: Amount {response['data']['amount']}"
                        break
                    else:
                        messages.info(request, f"ERROR: {response['status']} -- {response['message']}")
                        return redirect('check_transactions')
                return render(request, 'accounts/check_transactions.html',{'display':display})
            else:
                response = response.json()
                messages.info(request, f"ERROR: {response['status']} -- {response['message']}")
                return redirect('check_transactions')  
  
    return render(request, 'accounts/check_transactions.html')
# About Us Page
def about_us(request):
    return render(request, 'accounts/about.html')
class LogoutView(View):
    def get(self, request, *args, **kwargs):
        # Log out the user for GET requests as well
        request.session.flush()
        logout(request)
        # Redirect to the desired page after logout
        return redirect('login')

    def post(self, request, *args, **kwargs):
        # Log out the user for POST requests
        request.session.flush()
        logout(request)
        # Redirect to the desired page after logout
        return redirect('login')

# Htmx pages
# year display on html footer
def year(request):
    my_time = time.localtime()
    year = str(my_time.tm_year)
    return HttpResponse(year)
def warnings(request):
    return HttpResponse("Deleting your plan will wipe all transactions attached to the Plan. Download your <a style='color: blue;' href='http://localhost:8000/statement/'>account statement</a> before deleting or <span style='color: blue;'>proceed with deleting</span>"
)
def check_balance(request,plan_id):
    check_debit = f'{request.user.username}_{plan_id}_D'
  
    check_credit = f'{request.user.username}_{plan_id}_C'
   
    auth_token= env('FLUTTERWAVE_SECRET_KEY')
    hed = {'Authorization': 'Bearer ' + auth_token}
    url= 'https://api.flutterwave.com/v3/transactions'
    response = requests.get(url, headers=hed)
    all_debit = []
    all_credit = []
    if response.status_code == 200:
        response = response.json()
        for x in response['data']:
            if check_debit in x['tx_ref']:
                all_debit.append(x['amount_settled'])
            if check_credit in x['tx_ref']:
                all_credit.append(x['amount_settled'])  
        balance = round((Decimal(sum(all_credit))-Decimal(sum(all_debit))),2)
        
        value=balance
        if isinstance(value, Decimal):
            if value > 999999 and value < 9999999:
                    a = str(value)[:1]
                    b = str(value)[1:2] 
                    c = str(value)[2:3]
                    return f'{a}.{b}{c}M'
            if value > 9999999:
                    a = str(value)[:1]
                    b = str(value)[1:2] 
                    c = str(value)[2:3]
                    d = str(value)[3:4]
                    return f'{a}{b}.{c}{d}M'
            elif value > 99999999:
                    a = str(value)[:1]
                    b = str(value)[1:2] 
                    c = str(value)[2:3]
                    return f'{a}{b}{c}M +'   
            return HttpResponse(format(value, ','))
        return HttpResponse(value)
def time_posted(request, notification_id):
    now = datetime.now()
    notif = Notification.objects.get(id=notification_id)
    posted_at = datetime(notif.timestamp.year, notif.timestamp.month, notif.timestamp.day, notif.timestamp.hour, notif.timestamp.minute, notif.timestamp.second, notif.timestamp.microsecond)
    
    if '+' in str(posted_at.astimezone()):
        hours = str(posted_at.astimezone()).split('+')[1].split(':')[0]
        main_hour = str(posted_at).split(':')[0].split(' ')[1]
        minute = str(posted_at).split(':')[1]
        seconds = str(posted_at).split(':')[2].split('.')[0]
        micro_seconds = str(posted_at).split(':')[2].split('.')[1]
        year = str(posted_at).split(' ')[0].split('-')[0]
        month = str(posted_at).split(' ')[0].split('-')[1]
        day = str(posted_at).split(' ')[0].split('-')[2]
        real_hour = int(main_hour) + int(hours)
        if real_hour > 23:
            real_hour = real_hour - 24
            day += 1
        posted_at = datetime(int(year),int(month),int(day),int(real_hour),int(minute),int(seconds),int(micro_seconds))
        time_passed = now - posted_at
        print(time_passed.days)
        if time_passed.days == 0:
            if time_passed.seconds >= 3600:
                time = round(time_passed.seconds/3600)
                if time == 1:
                    time_passed = f"{time} hour ago"
                else:
                    time_passed = f"{time} hours ago"
            elif time_passed.seconds >= 60:
                time = round(time_passed.seconds/60)
                if time == 1:
                    time_passed = f"{time} minute ago"
                else:
                    time_passed = f"{time} minutes ago"
            else:
                time_passed = f"{time_passed.seconds} seconds ago"
        elif time_passed.days >= 365:
            time = round(time_passed.days/365)
            if time == 1:
                time_passed = f"{time} year ago"
            else:
                time_passed = f"{time} years ago"
        elif time_passed.days >= 7:
            time = round(time_passed.days/7)
            if time == 1:
                time_passed = f"{time} week ago"
            else:
                time_passed = f"{time} weeks ago"
        else:
            if time_passed.days == 1:
                time_passed = f"{time_passed.days} day ago"
            else:
                time_passed = f"{time_passed.days} days ago"   
    elif str(posted_at.astimezone()).count('-') > 2:
        hours = str(posted_at.astimezone()).split('+')[1].split(':')[0]
        main_hour = str(posted_at).split(':')[0].split(' ')[1]
        minute = str(posted_at).split(':')[1]
        seconds = str(posted_at).split(':')[2].split('.')[0]
        micro_seconds = str(posted_at).split(':')[2].split('.')[1]
        year = str(posted_at).split(' ')[0].split('-')[0]
        month = str(posted_at).split(' ')[0].split('-')[1]
        day = str(posted_at).split(' ')[0].split('-')[2]
        real_hour = int(main_hour) + int(hours)
        if real_hour > 24:
            real_hour = real_hour - 24
            day += 1
        posted_at = datetime(int(year),int(month),int(day),int(real_hour),int(minute),int(seconds),int(micro_seconds))
        time_passed = now - posted_at
    else:
       time_passed = now - posted_at 
    return HttpResponse(time_passed)

# delete functions

@login_required
def clear_notifications(request):
    user_ids = Notification.objects.filter(user=request.user).values_list('id', flat=True)
   
    Notification.objects.filter(id__in=user_ids, user=request.user).delete()
    return HttpResponse("Deleted All Notifications Successfully")

@login_required
def delete_notification(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    notification.delete()
    return HttpResponse("Deleted Successfully")

@login_required
def delete_nig_account(request, nig_id):
    account = get_object_or_404(BankAccountNigerian, id=nig_id)
    account.delete()
    return HttpResponse("Deleted Successfully")

@login_required
def delete_for_account(request, for_id):
    account = get_object_or_404(BankAccountForeign, id=for_id)
    account.delete()
    return HttpResponse("Deleted Successfully")

def otp_button(request):
    if request.POST['1'] and request.POST['2'] and request.POST['3'] and request.POST['4'] and request.POST['5'] and request.POST['6']:
        return HttpResponse('<button class="btn btn-primary px-4 validate" type="submit">Validate</button>')
    else:
        list = []
        for x in [request.POST['1'],request.POST['2'],request.POST['3'],request.POST['4'],request.POST['5'],request.POST['6']]:
            print(x,'.')
            if x != '':
                list.append(x)
        numbers = 6 - len(list)
        return HttpResponse(f'<button style="opacity: 0.5;" class="btn btn-primary px-4 validate" type="button">{numbers} Digits left</button>') 
@login_required
def picture(request):
        picture = ProfilePicture.objects.all()
        if f'{request.user} just uploaded' in str(picture):
            return render(request, 'accounts/pic-htmx.html',{'picture':picture})
        else:
            return render(request, 'accounts/pic-htmx.html') 
@login_required
def picture2(request):
    picture = ProfilePicture.objects.all()
    if f'{request.user} just uploaded' in str(picture):
        return render(request, 'accounts/pic-htmx2.html',{'picture':picture})
    else:
        return render(request, 'accounts/pic-htmx2.html') 
    
def read_notification(request):
    count = len(Notification.objects.filter(user=request.user,status='unread'))
    return HttpResponse(count)
def check(request):
    username = request.POST.get('username')
    if get_user_model().objects.filter(username=username).exists():
        return HttpResponse("<div style='color: red; font-size: 12px;'><i class='fa-regular fa-rectangle-xmark'></i> This username is taken</div>")
    else:
        return HttpResponse("<div style='color: green; font-size: 12px;'><i class='fa-regular fa-square-check'></i> This username is available</div>")
   
def check2(request):
    username = request.POST.get('username')
    if get_user_model().objects.filter(username=username).exists():
        return HttpResponse("This username is vaild")
    else:
        return HttpResponse("<div style='color: red; font-size: 12px;'>This username is not valid</div>") 

def email(request):
        emailcheck = str(request.POST.get('email'))
        if not emailcheck.count('@') == 1:
            return HttpResponse("<div style='color: red; font-size: 12px;'><i class='fa-regular fa-rectangle-xmark'></i> This is not an email</div>") 
        else:
            return HttpResponse("<i class='fa-regular fa-square-check'></i> Email is valid") 


# error handling urls
def handling_404(request, exception):
    return render(request, 'main/404.html', {})

def error_500(request):
    return render(request, "main/500.html",{})


