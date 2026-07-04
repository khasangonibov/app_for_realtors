from rest_framework import generics, permissions, filters
from .models import Contact
from .serializers import ContactSerializer


class ContactListCreateView(generics.ListCreateAPIView):
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'phone', 'email']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = Contact.objects.filter(
            agency=self.request.user.agency
        ).prefetch_related('activities')

        if self.request.user.is_agent:
            qs = qs.filter(agent=self.request.user)

        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)

        return qs


class ContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Contact.objects.filter(agency=self.request.user.agency)