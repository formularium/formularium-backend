from django.contrib import admin

# Register your models here.
from teams.models import Team, TeamMembership, TeamCertificate


class TeamMembershipInline(admin.TabularInline):
    model = TeamMembership


class TeamAdmin(admin.ModelAdmin):
    inlines = [TeamMembershipInline]


admin.site.register(Team, TeamAdmin)
admin.site.register(TeamCertificate)
