
from django.urls import path
from apps.users import views

urlpatterns = [
   path('register-user/', views.RegisterView.as_view(), name="register-user"),
   path('check-email/', views.CheckEmail.as_view(), name="check-email"),
   path('change-regulation/', views.ChangeRegulation.as_view(), name="change-regulation"),
   path('extract-document/', views.ExtractDocumentData.as_view(), name="extract-document"),
   path('get-wp-verify-link/', views.GenerateWPLink.as_view(), name="get-wp-verify-link"),
   path('phone-send-otp/', views.CheckUserPhoneNumber.as_view(), name="verify-user-phone-number"),
   path('verify-phone-otp/', views.VerifyUserPhoneNumber.as_view(), name="verify-phone-otp"),
   
]