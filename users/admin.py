"""Django admin configuration for user app."""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from users.models import VerificationToken


class UserAdmin(BaseUserAdmin):
    """Handle User admin."""

    list_display = ('email', 'is_superuser', 'is_staff', )
    fieldsets = (
        (None, {'fields': ('email', 'password', )}, ),
        (None, {'fields': ('activation_email_sent_at',)},),
        ('Permissions', {'fields': ('is_superuser', 'is_staff', 'groups', )}, ),
        (None, {'fields': ('is_active', 'was_activated', )}, ),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide', ),
            'fields': (
                'email',
                'password1',
                'password2',
            ),
        }),
    )
    ordering = ('id',)


admin.site.register(get_user_model(), UserAdmin)
admin.site.register(VerificationToken)