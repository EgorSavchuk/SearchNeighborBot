from django.contrib import admin
from .models import UserGeneralInformation, UserStatus, UserCriteria, ApartmentOwner

admin.site.register(UserGeneralInformation)
admin.site.register(UserStatus)
admin.site.register(UserCriteria)
admin.site.register(ApartmentOwner)
