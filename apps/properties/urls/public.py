from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth import views as django_auth_views
from apps.accounts.forms import StyledSetPasswordForm

from apps.properties.views import public as views
from apps.accounts import views as account_views


app_name = 'public'

urlpatterns = [
    # Каталог
    path('', views.catalog, name='catalog'),

    # Карточка объекта
    path(
        'object/<slug:agency_slug>/<uuid:pk>/<uuid:token>/',
        views.property_detail,
        name='property_detail',
    ),

    # Регистрация и профиль клиента
    path('register/', account_views.client_register, name='register'),
    path('profile/', account_views.client_profile, name='profile'),
    path('login/', account_views.PublicLoginView.as_view(), name='public_login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),

    
    # Сравнение объектов
    path('compare/', views.compare, name='compare'),
    path('compare/add/<uuid:pk>/', views.compare_add, name='compare_add'),
    path('compare/remove/<uuid:pk>/', views.compare_remove, name='compare_remove'),
    path('compare/clear/', views.compare_clear, name='compare_clear'),
    
    # Чат 
    path('chat/', account_views.client_chat_list, name='client_chat_list'),
    path('chat/room/<uuid:room_pk>/', account_views.client_chat, name='client_chat_room'),
    path('chat/new/', account_views.client_chat, name='client_chat_new'),
    path('chat/new/<uuid:agent_pk>/', account_views.client_chat, name='client_chat_agent'),
    path('chat/room/<uuid:room_pk>/poll/', account_views.client_chat_poll, name='client_chat_poll'),
    
    # Восстановление пароля — 4 шага стандартного флоу Django
    path('password-reset/',
        django_auth_views.PasswordResetView.as_view(
            template_name='public/password_reset.html',
            email_template_name='public/password_reset_email.txt',  # текстовая версия
            html_email_template_name='public/password_reset_email.html',  # HTML версия
            subject_template_name='public/password_reset_subject.txt',
            success_url='/password-reset/done/',
        ),
        name='password_reset'),

    path('password-reset/done/',
         django_auth_views.PasswordResetDoneView.as_view(
             template_name='public/password_reset_done.html',
         ),
         name='password_reset_done'),

    path('password-reset/confirm/<uidb64>/<token>/',
         django_auth_views.PasswordResetConfirmView.as_view(
             template_name='public/password_reset_confirm.html',
             success_url='/password-reset/complete/',
         ),
         name='password_reset_confirm'),

    path('password-reset/complete/',
         django_auth_views.PasswordResetCompleteView.as_view(
             template_name='public/password_reset_complete.html',
         ),
         name='password_reset_complete'),
    
    path('password-reset/confirm/<uidb64>/<token>/',
     django_auth_views.PasswordResetConfirmView.as_view(
         template_name='public/password_reset_confirm.html',
         form_class=StyledSetPasswordForm,
         success_url='/password-reset/complete/',
     ),
     name='password_reset_confirm'),
]