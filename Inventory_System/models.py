from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

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
    

class EncodingErrorRequest(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("In Progress", "In Progress"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
    ]

    # Request info
    date = models.DateField()
    time = models.TimeField()
    area_section = models.CharField(max_length=255)

    # Link to office (like ServiceRequest does)
    office = models.ForeignKey('Office', on_delete=models.CASCADE, null=True, blank=True)

    # Patient details
    hospital_no = models.CharField(max_length=50)
    patient_name = models.CharField(max_length=255)

    # Error details
    encoding_error_details = models.TextField()
    correct_data_details = models.TextField()

    # Signatures / Approvals
    encoded_by = models.CharField(max_length=255)   # could be a User, but form shows free-text
    encoded_date = models.DateField(null=True, blank=True)

    noted_by = models.CharField(max_length=255, null=True, blank=True)
    noted_date = models.DateField(null=True, blank=True)

    # 🔑 Corrected by IT (link to User in IT group)
    corrected_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'groups__name': 'IT'},
        related_name='corrected_encoding_errors'
    )
    corrected_date = models.DateField(null=True, blank=True)

    verified_by = models.CharField(max_length=255, null=True, blank=True)
    verified_date = models.DateField(null=True, blank=True)

    # ✅ Add status like in ServiceRequest
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Pending")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Encoding Error - {self.patient_name} ({self.hospital_no})"
    

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    url = models.CharField(max_length=255, blank=True, null=True)  # optional link
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient.username} - {self.message}"