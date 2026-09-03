from django.contrib import admin
from .models import PatientProfile, ScreeningResult, Specialist, ChatSession, ChatMessage, Feedback

# Standard Registrations
admin.site.register(PatientProfile)
admin.site.register(ScreeningResult)
admin.site.register(Specialist)

class ChatMessageInline(admin.TabularInline):
    """Allows viewing messages directly inside a session box."""
    model = ChatMessage
    extra = 0
    readonly_fields = ('query', 'response', 'timestamp') # Logs should be read-only

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at')
    list_filter = ('user', 'created_at')
    inlines = [ChatMessageInline] # Group messages into the session box

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'query', 'timestamp')
    list_filter = ('timestamp',)

# Register the Feedback model so the Admin can read the comments
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    # This makes the admin table look professional and easy to read
    list_display = ('user', 'short_comment', 'created_at')
    search_fields = ('user__username', 'comment')
    list_filter = ('created_at',)
    readonly_fields = ('user', 'comment', 'created_at') # Prevents accidental edits by admins

    def short_comment(self, obj):
        # Truncates long comments so the table doesn't get messed up
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    short_comment.short_description = 'Feedback Comment'