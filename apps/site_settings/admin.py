from django.contrib import admin

from .models import HomeBanner, SiteCounter, SiteLogo, SiteSetting, SocialNetwork, UsefulSite

admin.site.register(SiteSetting)
admin.site.register(SiteLogo)
admin.site.register(SiteCounter)
admin.site.register(SocialNetwork)
admin.site.register(UsefulSite)
admin.site.register(HomeBanner)
