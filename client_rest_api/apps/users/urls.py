
from django.urls import path
from apps.users import views

urlpatterns = [
   path('check-email/', views.CheckEmail.as_view(), name="check-email"),
   path('get-wp-verify-link/', views.GenerateWPLink.as_view(), name="get-wp-verify-link"),
   path('phone-send-otp/', views.CheckUserPhoneNumber.as_view(), name="verify-user-phone-number"),
   path('verify-phone-otp/', views.VerifyUserPhoneNumber.as_view(), name="verify-phone-otp"),
]