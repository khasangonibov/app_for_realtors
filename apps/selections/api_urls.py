from django.urls import path
from . import api_views

urlpatterns = [
    # CRM — список и создание подборок
    path('selections/', api_views.SelectionListCreateView.as_view()),
    path('selections/<uuid:pk>/', api_views.SelectionDetailView.as_view()),

    # Управление объектами в подборке
    path('selections/<uuid:pk>/items/', api_views.SelectionAddItemView.as_view()),
    path('selections/<uuid:pk>/items/<uuid:item_pk>/', api_views.SelectionRemoveItemView.as_view()),

    # Публичный доступ — без авторизации
    path('selections/public/<uuid:token>/', api_views.SelectionPublicView.as_view()),
    path('selections/public/<uuid:token>/react/<uuid:item_pk>/', api_views.SelectionItemReactView.as_view()),
]