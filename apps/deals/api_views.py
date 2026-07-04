from rest_framework import generics, permissions
from .models import Deal
from .serializers import DealSerializer


class DealListCreateView(generics.ListCreateAPIView):
    serializer_class = DealSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Deal.objects.filter(
            agency=self.request.user.agency
        ).select_related('property', 'buyer_contact', 'agent')

        if self.request.user.is_agent:
            qs = qs.filter(agent=self.request.user)

        stage = self.request.query_params.get('stage')
        if stage:
            qs = qs.filter(stage=stage)

        return qs


class DealDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DealSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Deal.objects.filter(agency=self.request.user.agency)