from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('login/', views.login_view, name="user-login"),
    path('otp/', views.otp_view, name="otp"),
    path('', views.base, name="base"),
    path('home/', views.home, name="home"),
    path('register/', views.register, name="register"),
    path('profilepage/', views.profilepage, name="profilepage"),
    path('statement/', views.account_statement, name="statement"),
    path('editprofile/', views.editprofile, name="editprofile"),
    path('editpicture/', views.editpicture, name="editpicture"),
    path('notification/', views.notification, name="notification"),
    path('bank_accounts/', views.bank_accounts, name="bank_accounts"),
    path('check_transactions/<int:plan_id>/', views.check_transactions, name="check_transactions"),
    path('delete_plan/<int:plan_id>/', views.delete_plan, name="delete_plan"),
    path('deposit_success/', views.deposit_success, name="deposit_success"),
    path('about_us/', views.about_us, name="about_us"),
    path('trading_password/<int:plan_id>/<str:amount>/', views.trading_password, name="trading_password"),
    path('notification/<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    path('nig_accounts/<int:nig_id>/delete/', views.delete_nig_account, name='delete_nig_account'),
    path('for_accounts/<int:for_id>/delete/', views.delete_for_account, name='delete_for_account'),
    path('transaction/<str:pk>/delete/', views.delete_transaction, name='delete_transaction'),
    path('plans/', views.plans, name='plans'),
    path('create_plan/', views.create_plan, name='create_plan'),
    path('create_tp/', views.create_tp, name='create_tp'),
    path('plan_deposit/<int:plan_id>/', views.plan_deposit, name='plan_deposit'),
    path('plan-list/<int:plan_id>/', views.plan_list, name='plan_list'),
    path('plan-cancel/<int:plan_id>/', views.deletePlan, name='plan_cancel'),
    path('notification/clear/', views.clear_notifications, name='clear_notifications'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    #all htmx urls
    path('check_username/', views.check, name='check_username'),
    path('check_username2/', views.check2, name='check_username2'),
    path('email_username/', views.email, name='email_username'),
    path('picture_view/', views.picture, name='picture_view'),
    path('picture_view2/', views.picture2, name='picture_view2'),
    path('otp_button/', views.otp_button, name='otp_button'),
    path('read_notification/', views.read_notification, name='read_notification'),
    path('year/', views.year, name='year'),
    path('warnings/', views.warnings, name='warnings'),
    path('time_posted/<int:notification_id>/', views.time_posted, name='time_posted'),
    path('check_balance/<int:plan_id>/', views.check_balance, name='check_balance'),
    # reset password urls
    path('password_reset/', auth_views.PasswordResetView.as_view(html_email_template_name='registration/password_reset_email.html'), name='password_reset'),
    path('password_reset/done/',auth_views.PasswordResetDoneView.as_view(),name='password_reset_done'),

    path('reset/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(),name='password_reset_confirm'),

    path('reset/done/',auth_views.PasswordResetCompleteView.as_view(),name='password_reset_complete'),

]