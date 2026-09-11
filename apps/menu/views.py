from rest_framework import viewsets

from .models import MenuItem
from .serializers import MenuItemSerializer


class MenuItemViewSet(viewsets.ReadOnlyModelViewSet):
    # Only top-level items are listed; each one's full subtree comes along via
    # the serializer's recursive `children`. Prefetch two levels — deep enough
    # for the real site's menu, and still one query instead of one per node.
    queryset = MenuItem.objects.filter(parent__isnull=True).prefetch_related("children__children")
    serializer_class = MenuItemSerializer
    # A nav tree has no "next page" — paginating it would be meaningless and
    # would wrap the response in {count, next, previous, results} for no reason.
    pagination_class = None
