from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.position}"

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

#  --- User Permission Models ---
class UserPermission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    permissions = models.ManyToManyField(PermissionOption)  # Many-to-many relationship
    office = models.ForeignKey('Office', on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"Permissions for {self.user.username}"


# --- Service Request Models ---

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class ServiceRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    submission_date = models.DateTimeField(auto_now_add=True)
    requestor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    office = models.ForeignKey(Office, on_delete=models.CASCADE)
    service_category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True)
    description = models.TextField(default="No description provided")
    employee_name = models.CharField(max_length=255, null=True, blank=True)
    employee_position = models.CharField(max_length=255, null=True, blank=True, default="Not specified")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_requests')
    action_taken = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Request #{self.id} - {self.office.office_name} - {self.status}"