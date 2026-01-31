from django.contrib import admin, messages
from .models import Listing, Transaction, Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    This makes the Profile model manageable in the admin area,
    allowing you to see and edit user's 2FA status and UPI ID.
    """
    list_display = ('user', 'is_2fa_enabled', 'seller_upi_id')
    search_fields = ('user__username',)
    list_editable = ('seller_upi_id',)

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ('handle', 'platform', 'seller', 'price', 'status')
    list_filter = ('status', 'platform')
    search_fields = ('handle', 'seller__username')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """
    This is your command center for managing the manual escrow process.
    """
    list_display = ('id', 'listing', 'buyer', 'seller', 'status', 'get_seller_upi', 'updated_at')
    list_filter = ('status',)
    search_fields = ('listing__handle', 'buyer__username', 'seller__username')
    list_editable = ('status',)
    actions = ['mark_delivery_pending', 'mark_payment_released']

    @admin.display(description="Seller's UPI ID")
    def get_seller_upi(self, obj):
        """
        A helper function to display the seller's UPI ID directly in the transaction list.
        This makes it easy for you to copy the ID for manual payment.
        """
        if hasattr(obj.seller, 'profile'):
            return obj.seller.profile.seller_upi_id
        return "Not Set"

    @admin.action(description='Mark as Verified & Ready for Delivery')
    def mark_delivery_pending(self, request, queryset):
        queryset.update(status='delivery_pending')
        self.message_user(request, "Selected transactions have been marked as ready for delivery.")

    @admin.action(description='Mark as Complete (Confirm Manual Payout)')
    def mark_payment_released(self, request, queryset):
        """
        This action is for you, the admin, to use AFTER you have manually
        sent the payment to the seller's UPI ID. It updates the records.
        """
        updated_count = 0
        for transaction in queryset.filter(status='delivery_pending'):
            transaction.status = 'complete'
            transaction.listing.status = 'sold'
            transaction.listing.save()
            transaction.save()
            updated_count += 1
            
        if updated_count > 0:
            self.message_user(request, f"{updated_count} transactions were successfully marked as complete.")

