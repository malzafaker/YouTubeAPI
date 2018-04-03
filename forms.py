from django import forms

from apps.youtube.models import UploadedVideo


class YoutubeDirectUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedVideo
