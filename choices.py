from django.utils.translation import ugettext_lazy as _


class AccessControl:
    Public = 0
    Unlisted = 1
    Private = 2

    CHOICES = (
        (Public, _('Открытый доступ')),
        (Unlisted, _('Доступ по ссылке')),
        (Private, _('Ограниченный доступ')),
    )

