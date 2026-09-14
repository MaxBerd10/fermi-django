from django.contrib import admin

from .models import ConnectLeader, District, Quarter, Region


class DistrictInline(admin.TabularInline):
    model = District
    extra = 0


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name", "order")
    inlines = [DistrictInline]


class QuarterInline(admin.TabularInline):
    model = Quarter
    extra = 0


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("name", "region", "order")
    list_filter = ("region",)
    inlines = [QuarterInline]


@admin.register(Quarter)
class QuarterAdmin(admin.ModelAdmin):
    list_display = ("name", "district", "order")
    list_filter = ("district__region", "district")


@admin.register(ConnectLeader)
class ConnectLeaderAdmin(admin.ModelAdmin):
    list_display = ("name", "order")
