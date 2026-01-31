from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Listing, Transaction, Offer, Profile

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    email = serializers.EmailField(required=True)
    
    # --- New fields for the Hackathon Demo ---
    phone_number = serializers.CharField(write_only=True, required=True)
    upi_id = serializers.CharField(write_only=True, required=True)
    otp = serializers.CharField(write_only=True, required=True) # Validated in View

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'phone_number', 'upi_id', 'otp')

    def create(self, validated_data):
        # 1. Extract the extra fields that don't belong to the User model
        phone = validated_data.pop('phone_number')
        upi = validated_data.pop('upi_id')
        otp = validated_data.pop('otp')
        
        # 2. Create the User instance
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        
        # 3. Update the automatically created Profile with the extra data
        # (The profile is created via signals in models.py)
        if hasattr(user, 'profile'):
            user.profile.phone_number = phone
            user.profile.seller_upi_id = upi
            user.profile.is_phone_verified = True # Mark as verified since they passed OTP check
            user.profile.save()
        
        return user

class ListingSerializer(serializers.ModelSerializer):
    seller = serializers.ReadOnlyField(source='seller.username')
    
    # --- Write-only field for the account credentials (Admin verification) ---
    account_password = serializers.CharField(write_only=True, required=True)
    
    trust_score = serializers.SerializerMethodField() # Dynamic Trust Score

    class Meta:
        model = Listing
        fields = '__all__'

    def get_trust_score(self, obj):
        score = 0
        
        # Check profile attributes
        if hasattr(obj.seller, 'profile'):
            # 1. 2FA Enabled (+30)
            if obj.seller.profile.is_2fa_enabled:
                score += 30
            # 2. Phone Verified (+30) - High trust factor
            if obj.seller.profile.is_phone_verified:
                score += 30
            # 3. Seller has provided Payout Info (+10)
            if obj.seller.profile.seller_upi_id:
                score += 10

        # 4. Account Verified by Admin (+20)
        if obj.is_verified:
            score += 20
        # 5. Detailed Description (+10)
        if len(obj.description) > 50:
            score += 10
        
        return min(score, 100)

class TransactionSerializer(serializers.ModelSerializer):
    listing = ListingSerializer(read_only=True)
    class Meta:
        model = Transaction
        fields = ['id', 'listing', 'buyer', 'seller', 'amount', 'status', 'new_password', 'created_at', 'updated_at']

class OfferSerializer(serializers.ModelSerializer):
    buyer = serializers.ReadOnlyField(source='buyer.username')
    listing_handle = serializers.ReadOnlyField(source='listing.handle')
    
    class Meta:
        model = Offer
        fields = ['id', 'listing', 'listing_handle', 'buyer', 'amount', 'status', 'created_at']