from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_2fa_enabled = models.BooleanField(default=False)
    seller_upi_id = models.CharField(max_length=100, blank=True, null=True, help_text="Seller's UPI ID for payouts")
    
    # --- NEW FIELDS FOR HACKATHON DEMO ---
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_phone_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    if hasattr(instance, 'profile'):
        instance.profile.save()

class Listing(models.Model):
    STATUS_CHOICES = [('available', 'Available'), ('in_escrow', 'In Escrow'), ('sold', 'Sold')]
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    platform = models.CharField(max_length=50)
    handle = models.CharField(max_length=100)
    description = models.TextField()
    follower_count = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    is_verified = models.BooleanField(default=False)
    
    # --- NEW FIELD: To store the account's actual password for Admin verification ---
    # In a real production app, this should be an EncryptedCharField.
    account_password = models.CharField(max_length=255, default="", help_text="The login password for the social account")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.platform} account: {self.handle}"

class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('admin_review', 'Paid - Awaiting Admin Review'),
        ('delivery_pending', 'Verified - Awaiting Delivery to Buyer'),
        ('complete', 'Complete - Payment Released'),
        ('disputed', 'Disputed'),
        ('cancelled', 'Cancelled'),
    ]
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, related_name='purchases', on_delete=models.CASCADE)
    seller = models.ForeignKey(User, related_name='sales', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    brokerage_fee = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    stripe_checkout_id = models.CharField(max_length=255, blank=True, null=True)
    new_password = models.CharField(max_length=255, blank=True, null=True, help_text="Set by admin after verification")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Transaction {self.id} for {self.listing.handle}"

# --- Offer Model for Negotiation ---
class Offer(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')]
    listing = models.ForeignKey(Listing, related_name='offers', on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, related_name='offers_made', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Offer of {self.amount} for {self.listing.handle} by {self.buyer.username}"

# --- NEW: OTP Storage Model ---
class PhoneOTP(models.Model):
    phone_number = models.CharField(max_length=15)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)