from django.contrib import admin

from apps.youtube.models import YouTubeVideo


@admin.register(YouTubeVideo)
class VideoAdmin(admin.ModelAdmin):
    readonly_fields = ('video_id', 'youtube_url')
    list_filter = ('title',)
    search_fields = ['title']
    list_display = ('title', 'video_id', 'youtube_url')
