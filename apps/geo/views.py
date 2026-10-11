from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView

from .models import ConnectLeader, District, Quarter, Region
from .serializers import ConnectLeaderSerializer, DistrictSerializer, QuarterSerializer, RegionSerializer


class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    pagination_class = None  # a fixed 14-region list


def _as_id(value, name):
    """A query-string id must be a whole number: anything else is a 400, not the 500 a failed int cast gave."""
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError({name: f"{name} butun son bo'lishi kerak."})


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
        return District.objects.filter(region_id=_as_id(region_id, "regionId"))


class QuarterListView(ListAPIView):
    """GET /api/v1/quarters?districtId=<id> -- see DistrictListView."""

    serializer_class = QuarterSerializer
    pagination_class = None

    def get_queryset(self):
        district_id = self.request.query_params.get("districtId")
        if not district_id:
            raise ValidationError({"districtId": "districtId talab qilinadi."})
        return Quarter.objects.filter(district_id=_as_id(district_id, "districtId"))


class ConnectLeaderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ConnectLeader.objects.all()
    serializer_class = ConnectLeaderSerializer
    pagination_class = None
