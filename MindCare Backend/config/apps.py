from django.contrib.admin.apps import AdminConfig


class MindCareAdminConfig(AdminConfig):
    default_site = "config.admin_site.MindCareAdminSite"
