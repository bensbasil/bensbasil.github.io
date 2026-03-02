from django.contrib import admin
from .models import Project, ContactInquiry

admin.site.register(Project)

@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'created_at')
    # This makes the messages read-only so you don't accidentally edit a client's words
    readonly_fields = ('created_at',)