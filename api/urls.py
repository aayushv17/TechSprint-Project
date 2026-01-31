from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, ListingViewSet, TransactionViewSet, OfferViewSet,
    generate_2fa_secret, verify_2fa_setup, CustomTokenObtainPairView, verify_2fa_login,
    create_razorpay_order, RazorpayWebhookView,
    get_transaction_credentials, update_seller_upi,
    generate_ai_description, analyze_listing_screenshot, chat_with_scout,
    send_phone_otp, parse_listing_from_text
)

router = DefaultRouter()
router.register(r'listings', ListingViewSet, basename='listing')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'offers', OfferViewSet, basename='offer')

urlpatterns = [
    # Router Endpoints (Listings, Transactions, Offers)
    path('', include(router.urls)),
    
    # Auth & 2FA
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/send-otp/', send_phone_otp, name='send_phone_otp'), # New OTP Endpoint

    # 2FA Logic
    path('2fa/generate/', generate_2fa_secret, name='2fa_generate'),
    path('2fa/verify-setup/', verify_2fa_setup, name='2fa_verify_setup'),
    path('2fa/verify-login/', verify_2fa_login, name='2fa_verify_login'),

    # Razorpay Payment
    path('create-razorpay-order/<int:listing_id>/', create_razorpay_order, name='create_razorpay_order'),
    path('razorpay-webhook/', RazorpayWebhookView.as_view(), name='razorpay_webhook'),
    
    # Credentials & Payouts
    path('transactions/<int:transaction_id>/credentials/', get_transaction_credentials, name='get_transaction_credentials'),
    path('payouts/update-upi/', update_seller_upi, name='update_seller_upi'),

    # AI Features
    path('ai/generate-description/', generate_ai_description, name='ai_generate_description'),
    path('ai/analyze-screenshot/', analyze_listing_screenshot, name='ai_analyze_screenshot'),
    path('ai/chat/', chat_with_scout, name='chat_with_scout'),
    path('ai/parse-listing/', parse_listing_from_text, name='ai_parse_listing'), # New Magic Fill Endpoint
]