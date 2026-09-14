from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView

from .models import ConnectLeader, District, Quarter, Region
from .serializers import ConnectLeaderSerializer, DistrictSerializer, QuarterSerializer, RegionSerializer


class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    pagination_class = None  # a fixed 14-region list


class DistrictListView(ListAPIView):
    """GET /api/v1/districts?regionId=<id> -- always filtered, never a
    bare "every district" listing (matches the old site's own API, which
    400s without regionId; the frontend never calls this without one
    either -- see api/lookups.ts::getDistricts)."""

    serializer_class = DistrictSerializer
    pagination_class = None

    def get_queryset(self):
        region_id = self.request.query_params.get("regionId")
        if not region_id:
            raise ValidationError({"regionId": "regionId talab qilinadi."})
        return District.objects.filter(region_id=region_id)


class QuarterListView(ListAPIView):
    """GET /api/v1/quarters?districtId=<id> -- see DistrictListView."""

    serializer_class = QuarterSerializer
    pagination_class = None

    def get_queryset(self):
        district_id = self.request.query_params.get("districtId")
        if not district_id:
            raise ValidationError({"districtId": "districtId talab qilinadi."})
        return Quarter.objects.filter(district_id=district_id)


class ConnectLeaderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ConnectLeader.objects.all()
    serializer_class = ConnectLeaderSerializer
    pagination_class = None
