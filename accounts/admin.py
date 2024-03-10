from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(User)
admin.site.register(Transaction)
admin.site.register(Notification)
admin.site.register(ProfilePicture)
admin.site.register(Plan)
admin.site.register(TradingUser)
admin.site.register(AutoPlan)
admin.site.register(BankAccountNigerian)
admin.site.register(BankAccountForeign)