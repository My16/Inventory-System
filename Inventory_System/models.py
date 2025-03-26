from django.db import models
from django.contrib.auth.models import User

class Office(models.Model):
    office_name = models.CharField(max_length=255, unique=True)
    abbreviation = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Updates every time the record is modified

    def __str__(self):
        return self.office_name

class PermissionOption(models.Model):
    name = models.CharField(max_length=255, unique=True)  # Name of the permission (e.g., "Dashboard", "Equipment Management")

    def __str__(self):
        return self.name

class UserPermission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    permissions = models.ManyToManyField(PermissionOption)  # Many-to-many relationship

    def __str__(self):
        return f"Permissions for {self.user.username}"
