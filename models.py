from django.db import models
from django.utils.translation import ugettext as _

from apps.youtube.choices import AccessControl


class YouTubeVideo(models.Model):
    video_id = models.CharField(verbose_name=_('ID видео на youtube'), max_length=255, blank=True, default='')
    title = models.CharField(verbose_name=_('Название'), max_length=200, blank=True, default='')
    description = models.TextField(verbose_name=_('Описание'), blank=True, default='')
    youtube_url = models.URLField(verbose_name=_('Ссылка на видео'), max_length=255, null=True, blank=True)
    access_control = models.SmallIntegerField(choices=AccessControl.CHOICES, default=AccessControl.Unlisted)

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return self.youtube_url

    def delete(self, *args, **kwargs):
        return super(YouTubeVideo, self).delete(*args, **kwargs)
