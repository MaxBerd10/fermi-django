from django.contrib import admin

from .models import ResultCategory, ResultFile, ResultsPage

admin.site.register(ResultsPage)
admin.site.register(ResultCategory)
admin.site.register(ResultFile)
