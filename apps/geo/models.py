from django.db import models


class Region(models.Model):
    """One of Uzbekistan's 14 regions. Single-language (Uzbek) on purpose --
    the old site's own /regions API always returns Uzbek names regardless of
    ?lang= (frontend/src/lib/regionNames.ts already works around this by
    translating the 14 names client-side, by id; this table matches that
    same real-world behavior instead of inventing ru/en fields nothing
    actually populates)."""

    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.name


class District(models.Model):
    """A district within a Region -- same single-language rationale as
    Region above."""

    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="districts")
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.name


class Quarter(models.Model):
    """A quarter/mahalla within a District -- only used by the Qabul
    (admission) form's address cascade; sparse on the old site itself
    (most districts have none), not a gap on our side."""

    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name="quarters")
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.name


class ConnectLeader(models.Model):
    """Who a Qabul (admission) inquiry can be routed to -- a short, flat
    name list (see frontend's getConnectLeaders/ConnectLeader)."""

    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.name
