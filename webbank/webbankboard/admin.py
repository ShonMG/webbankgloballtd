from django.contrib import admin, messages
from django.conf import settings
from django.db import transaction
from .models import WebBankMembership

@admin.register(WebBankMembership)
class WebBankMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'created_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('user__email',)
    raw_id_fields = ('user',)

    def save_model(self, request, obj, form, change):
        # Check if the status is being changed to ACTIVE
        if 'status' in form.changed_data and obj.status == WebBankMembership.StatusChoices.ACTIVE:
            with transaction.atomic():
                # Re-fetch the object to get the current state and lock it
                # Using select_for_update to prevent race conditions
                current_obj = WebBankMembership.objects.select_for_update().get(pk=obj.pk)
                
                # Only proceed if the status was NOT already active (i.e., it's a transition to active)
                if current_obj.status != WebBankMembership.StatusChoices.ACTIVE:
                    active_members_count = WebBankMembership.objects.filter(
                        status=WebBankMembership.StatusChoices.ACTIVE
                    ).count()

                    if active_members_count >= settings.WEBBANK_MEMBER_CAP:
                        messages.error(request, 
                                       f"Cannot activate WebBank membership for {obj.user.email}. "
                                       f"The WebBank member cap of {settings.WEBBANK_MEMBER_CAP} active members has been reached.")
                        return # Do not save the object

        super().save_model(request, obj, form, change)