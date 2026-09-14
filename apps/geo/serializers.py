from rest_framework import serializers

from .models import ConnectLeader, District, Quarter, Region


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ["id", "name"]


class DistrictSerializer(serializers.ModelSerializer):
    regionId = serializers.IntegerField(source="region_id")

    class Meta:
        model = District
        fields = ["id", "regionId", "name"]


class QuarterSerializer(serializers.ModelSerializer):
    districtId = serializers.IntegerField(source="district_id")

    class Meta:
        model = Quarter
        fields = ["id", "districtId", "name"]


class ConnectLeaderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConnectLeader
        fields = ["id", "name"]
