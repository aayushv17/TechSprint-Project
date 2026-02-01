from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse
import razorpay
import requests
import time
import json
import base64
import random
from rest_framework import generics, permissions, viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Listing, Transaction, Profile, Offer, PhoneOTP
from .serializers import ListingSerializer, RegisterSerializer, TransactionSerializer, OfferSerializer
from decimal import Decimal

# --- 2FA & Auth Imports ---
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
import qrcode
from io import BytesIO

# ==========================================
# --- CONFIGURATION ---
GEMINI_API_KEY = "AIzaSyDDj60IJJPq2wIc2AtrX37_pyBliytAV90"
# ==========================================

# --- CORE VIEWS ---
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        # In a real app, verify OTP here before creating user
        return super().create(request, *args, **kwargs)

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.filter(status='available').order_by('-created_at')
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        return Transaction.objects.filter(buyer=user) | Transaction.objects.filter(seller=user)

class OfferViewSet(viewsets.ModelViewSet):
    serializer_class = OfferSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Offer.objects.filter(buyer=user) | Offer.objects.filter(listing__seller=user)

    def perform_create(self, serializer):
        serializer.save(buyer=self.request.user)

# --- AI FEATURES ---

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_ai_description(request):
    platform = request.data.get('platform')
    followers = request.data.get('followers')
    handle = request.data.get('handle')
    price = request.data.get('price')
    
    if not all([platform, followers, handle]):
        return Response({'error': 'Platform, followers, and handle are required.'}, status=400)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_API_KEY}"
    prompt = f"Write a short, professional, and persuasive sales description (under 50 words) for a {platform} account with handle @{handle}, {followers} followers, priced at {price}. Highlight the value."
    payload = { "contents": [{ "parts": [{ "text": prompt }] }] }

    for attempt in range(3):
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                result = response.json()
                text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                return Response({'description': text.strip()})
            elif response.status_code == 429:
                time.sleep(2 ** attempt)
            else:
                return Response({'error': f'AI Error: {response.text}'}, status=500)
        except Exception:
            time.sleep(2 ** attempt)

    return Response({'error': 'AI service currently unavailable.'}, status=503)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_listing_screenshot(request):
    image_file = request.FILES.get('screenshot')
    platform = request.data.get('platform')

    if not image_file or not platform:
        return Response({'error': 'Screenshot and platform are required.'}, status=400)

    try:
        image_data = base64.b64encode(image_file.read()).decode('utf-8')
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_API_KEY}"
        
        prompt = f"""
        You are an auditor for a social media marketplace. Analyze this screenshot of a {platform} account.
        Respond with ONLY a JSON object (no markdown) with these keys:
        - "trust_score": (integer 0-100 based on authenticity)
        - "valuation": (string, estimated value range in INR)
        - "analysis": (string, brief 1-sentence comment on authenticity)
        """

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": image_data}}
                ]
            }]
        }

        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            ai_text = result['candidates'][0]['content']['parts'][0]['text']
            ai_text = ai_text.replace('```json', '').replace('```', '').strip()
            return HttpResponse(ai_text, content_type='application/json')
        return Response({'error': f'AI Error: {response.text}'}, status=response.status_code)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def chat_with_scout(request):
    user_query = request.data.get('query')
    if not user_query: return Response({'error': 'Query is required.'}, status=400)

    # 1. Fetch available listings to give the AI context
    listings = Listing.objects.filter(status='available').values('id', 'platform', 'handle', 'follower_count', 'price', 'description')
    listings_context = json.dumps(list(listings), default=str)

    # 2. Construct the prompt
    system_instruction = f"""
    You are 'AccSwap Scout', a helpful sales assistant for a social media marketplace.
    Current inventory: {listings_context}
    Rules: Recommend specific accounts (Handle, Price, ID). Keep it short.
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_API_KEY}"
    payload = { "contents": [{ "parts": [{ "text": user_query }] }], "systemInstruction": { "parts": [{ "text": system_instruction }] } }

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            return Response({'response': text})
        return Response({'error': 'AI busy.'}, status=503)
    except Exception as e: return Response({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def parse_listing_from_text(request):
    raw_text = request.data.get('text')
    if not raw_text: return Response({'error': 'No text provided.'}, status=400)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_API_KEY}"
    prompt = f"Extract listing details from: '{raw_text}'. Return ONLY JSON with keys (guess if missing): platform, handle, follower_count, price, description."
    payload = { "contents": [{ "parts": [{ "text": prompt }] }] }

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            ai_text = response.json()['candidates'][0]['content']['parts'][0]['text']
            ai_text = ai_text.replace('```json', '').replace('```', '').strip()
            return HttpResponse(ai_text, content_type='application/json')
        return Response({'error': 'AI Parse Failed'}, status=503)
    except Exception as e: return Response({'error': str(e)}, status=500)

# --- 2FA & AUTH VIEWS ---
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def send_phone_otp(request):
    phone_number = request.data.get('phone_number')
    if not phone_number: return Response({'error': 'Phone number required'}, status=400)
    
    otp = str(random.randint(100000, 999999))
    PhoneOTP.objects.create(phone_number=phone_number, otp=otp)
    
    print(f"\n >>> SMS OTP FOR {phone_number}: {otp} <<<\n")
    return Response({'status': 'OTP Sent', 'debug_otp': otp})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_2fa_secret(request):
    user = request.user
    device, created = TOTPDevice.objects.get_or_create(user=user, name=f"{user.username}_totp_device")
    if created: device.save()
    img = qrcode.make(device.config_url)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return Response({'secret_key': device.key, 'qr_code': f'data:image/png;base64,{qr_code_base64}'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_2fa_setup(request):
    user = request.user
    otp = request.data.get('otp_code')
    device = TOTPDevice.objects.filter(user=user).first()
    if not device or not device.verify_token(otp):
        return Response({'error': 'Invalid OTP'}, status=400)
    user.profile.is_2fa_enabled = True
    user.profile.save()
    return Response({'status': 'Enabled'})

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        Profile.objects.get_or_create(user=user)
        if user.profile.is_2fa_enabled:
            return Response({'2fa_required': True, 'user_id': user.id})
        refresh = RefreshToken.for_user(user)
        return Response({'refresh': str(refresh), 'access': str(refresh.access_token)})

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_2fa_login(request):
    user_id = request.data.get('user_id')
    otp_code = request.data.get('otp_code')
    try:
        user = User.objects.get(id=user_id)
        device = TOTPDevice.objects.filter(user=user).first()
        if not device or not device.verify_token(otp_code): raise Exception("Invalid OTP")
        refresh = RefreshToken.for_user(user)
        return Response({'refresh': str(refresh), 'access': str(refresh.access_token)})
    except Exception:
        return Response({'error': 'Invalid OTP code.'}, status=400)

# --- RAZORPAY PAYMENT VIEWS ---
try:
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
except Exception as e:
    print(f"CRITICAL: Failed to initialize Razorpay client. Check keys. Error: {e}")
    razorpay_client = None

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_razorpay_order(request, listing_id):
    if not razorpay_client: return Response({'error': 'Payment gateway not configured.'}, status=500)
    try:
        listing = Listing.objects.get(id=listing_id)
        if listing.status != 'available': return Response({'error': 'This listing is not available.'}, status=400)
        
        order_data = {
            "amount": int(listing.price * 100), 
            "currency": "INR", 
            "receipt": f"receipt_{listing.id}", 
            "notes": {"listing_id": listing.id, "buyer_id": request.user.id}
        }
        order = razorpay_client.order.create(data=order_data)

        Transaction.objects.create(
            listing=listing, 
            buyer=request.user, 
            seller=listing.seller, 
            amount=listing.price, 
            brokerage_fee=listing.price * Decimal('0.1'), 
            status='pending',
            stripe_checkout_id=order['id']
        )

        return Response({
            'order_id': order['id'], 
            'amount': order['amount'], 
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'currency': order['currency'],
            'name': 'AccSwap Marketplace',
            'description': f"Payment for {listing.platform} Account: @{listing.handle}",
            'prefill': {"name": request.user.username, "email": request.user.email}
        })
    except Listing.DoesNotExist: return Response({'error': 'Listing not found.'}, status=404)
    except Exception as e: return Response({'error': str(e)}, status=500)

class RazorpayWebhookView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request, format=None):
        try:
            razorpay_client.utility.verify_webhook_signature(
                request.body.decode('utf-8'), 
                request.META.get('HTTP_X_RAZORPAY_SIGNATURE'), 
                settings.RAZORPAY_WEBHOOK_SECRET
            )
            event = request.data.get('event')
            if event == 'payment.captured':
                payment_data = request.data.get('payload', {}).get('payment', {}).get('entity', {})
                notes = payment_data.get('notes', {})
                listing_id = notes.get('listing_id')
                buyer_id = notes.get('buyer_id')
                if listing_id and buyer_id:
                    try:
                        transaction = Transaction.objects.get(listing_id=listing_id, buyer_id=buyer_id, status='pending')
                        transaction.status = 'admin_review'
                        transaction.save()
                        transaction.listing.status = 'in_escrow'
                        transaction.listing.save()
                    except Transaction.DoesNotExist: pass
            return HttpResponse(status=200)
        except (razorpay.errors.SignatureVerificationError, ValueError): return HttpResponse(status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_transaction_credentials(request, transaction_id):
    try:
        tx = Transaction.objects.get(id=transaction_id, buyer=request.user)
        if tx.status == 'delivery_pending': 
            return Response({'new_password': tx.new_password})
        return Response({'error': 'Account verification in progress.'}, status=403)
    except Transaction.DoesNotExist:
        return Response({'error': 'Transaction not found.'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_seller_upi(request):
    profile = request.user.profile
    profile.seller_upi_id = request.data.get('upi_id')
    profile.save()
    return Response({'status': 'success'})