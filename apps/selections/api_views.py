from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Selection, SelectionItem
from .serializers import SelectionSerializer, SelectionItemSerializer


class SelectionListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/selections/  — список подборок
    POST /api/v1/selections/  — создать подборку
    """
    serializer_class = SelectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Selection.objects.filter(
            agency=self.request.user.agency
        ).select_related('contact', 'agent').prefetch_related('items')

        if self.request.user.is_agent:
            qs = qs.filter(agent=self.request.user)

        return qs


class SelectionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/selections/{id}/  — детали подборки
    PUT    /api/v1/selections/{id}/  — обновить
    DELETE /api/v1/selections/{id}/  — удалить
    """
    serializer_class = SelectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Selection.objects.filter(
            agency=self.request.user.agency
        ).prefetch_related('items__property')


class SelectionPublicView(APIView):
    """
    GET /api/v1/selections/public/{token}/
    Публичная подборка — без авторизации.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        selection = get_object_or_404(Selection, public_token=token)
        serializer = SelectionSerializer(
            selection, context={'request': request}
        )
        return Response(serializer.data)


class SelectionItemReactView(APIView):
    """
    POST /api/v1/selections/public/{token}/react/{item_id}/
    Клиент ставит реакцию на объект в подборке — без авторизации.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, token, item_pk):
        selection = get_object_or_404(Selection, public_token=token)
        item = get_object_or_404(SelectionItem, pk=item_pk, selection=selection)

        new_status = request.data.get('status')
        if new_status not in SelectionItem.ClientStatus.values:
            return Response(
                {'error': f'Допустимые значения: {SelectionItem.ClientStatus.values}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item.client_status = new_status
        item.save(update_fields=['client_status'])

        return Response(SelectionItemSerializer(item).data)


class SelectionAddItemView(APIView):
    """
    POST /api/v1/selections/{id}/items/
    Добавить объект в подборку.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        selection = get_object_or_404(
            Selection, pk=pk, agency=request.user.agency
        )
        serializer = SelectionItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(selection=selection)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SelectionRemoveItemView(APIView):
    """
    DELETE /api/v1/selections/{id}/items/{item_id}/
    Удалить объект из подборки.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk, item_pk):
        selection = get_object_or_404(
            Selection, pk=pk, agency=request.user.agency
        )
        item = get_object_or_404(SelectionItem, pk=item_pk, selection=selection)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)