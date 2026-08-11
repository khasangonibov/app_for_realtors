"""
Кастомный adapter для django-allauth.
"""

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email

from .models import UserProfile, Agency, User


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        """Вызывается перед созданием/входом через OAuth.
        Если пользователь с таким email уже существует в системе
        (например, регистрировался через обычную форму) —
        привязываем OAuth-аккаунт к нему вместо создания дубликата.
        """
        email = user_email(sociallogin.user)
        if not email:
            return

        try:
            existing_user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return

        # sociallogin ещё не подключён ни к одному пользователю —
        # подключаем его к найденному существующему аккаунту
        if not sociallogin.is_existing:
            sociallogin.connect(request, existing_user)

    def save_user(self, request, sociallogin, form=None):
        """Вызывается только при создании НОВОГО пользователя
        (если pre_social_login не нашёл существующий аккаунт)."""
        user = super().save_user(request, sociallogin, form)

        UserProfile.objects.get_or_create(
            user=user,
            defaults={'role': UserProfile.Role.CLIENT},
        )

        if user.email:
            from apps.contacts.models import Contact
            agency = Agency.get_solo()
            if agency:
                Contact.objects.get_or_create(
                    email=user.email,
                    agency=agency,
                    defaults={
                        'first_name': user.first_name or user.username,
                        'last_name': user.last_name or '',
                        'phone': user.phone or '',
                        'contact_type': Contact.ContactType.BUYER,
                        'status': Contact.Status.NEW,
                        'source': Contact.Source.SITE,
                        'notes': f'Зарегистрировался через {sociallogin.account.provider}.',
                    }
                )

        return user

    def is_open_for_signup(self, request, sociallogin):
        return True