from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Office, ServiceRequest, ServiceCategory
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json, random, colorsys, io, os, unicodedata
from django.shortcuts import get_object_or_404
from django.utils.timezone import localtime, now
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from functools import wraps
from .models import UserPermission, PermissionOption
from django.contrib.auth.models import Group
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from django.http import FileResponse, Http404
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter
from .models import EncodingErrorRequest, Notification, WebsiteUploadRequest, WebsiteUploadAttachment
from django.urls import reverse
from math import ceil
from .forms import WebsiteUploadRequestForm
from datetime import datetime

# Create your views here.
def loginPage(request):
    context = {}
    
    return render(request, 'loginPage.html', context)

def user_login(request):

    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
        
            # Fetch user's permissions
            try:
                user_permissions = UserPermission.objects.get(user=user)
                permission_list = list(user_permissions.permissions.values_list("name", flat=True))
            except UserPermission.DoesNotExist:
                permission_list = []

            # Store permissions in session
            request.session["user_permissions"] = permission_list
            print(f"✅ User {user.username} logged in. Assigned permissions: {permission_list}")

            return redirect("homepage")
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('loginpage') # Redirect to loginpage

    return redirect("loginpage")

def generate_distinct_colors(n):
    colors = []
    for i in range(n):
        hue = i * (360/n)
        sat = 70 + random.randint(-10, 10)
        light = 50 + random.randint(-10, 10)
        rgb = colorsys.hsv_to_rgb(hue/360, sat/100, light/100)
        colors.append(f"rgba({int(rgb[0]*255)}, {int(rgb[1]*255)}, {int(rgb[2]*255)}, 0.7)")
    return colors


@login_required
def latest_notifications(request):
    # Only unread notifications
    unread_qs = Notification.objects.filter(recipient=request.user, is_read=False).order_by("-created_at")

    data = [
        {
            "id": n.id,
            "message": n.message,
            "url": n.url,
            "created_at": n.created_at.strftime("%Y-%m-%d %H:%M"),
            "is_read": n.is_read,
        }
        for n in unread_qs
    ]

    return JsonResponse({
        "notifications": data,
        "unread_count": unread_qs.count(),
    })

@login_required(login_url='/login/')
def homepage(request):
    user = request.user
    user_permissions = request.session.get("user_permissions", [])
    is_it = user.groups.filter(name='IT').exists()
    display_name = user.get_full_name() if user.get_full_name() else user.username


    context = {
        "display_name": display_name,
        "user_permissions": user_permissions,
        "is_it": is_it,
    }

    return render(request, "home.html", context)

@login_required(login_url='/login/')
def add_office(request):
    user = request.user
    offices = Office.objects.all().order_by("id")  # Ascending order

    paginator = Paginator(offices, 10) #show 10 offices per page

    page_number = request.GET.get('page') #Get the current page number
    page_obj = paginator.get_page(page_number) #Get the page object

    context = {'offices': offices, 'page_obj': page_obj, 'display_name': user.get_full_name() if user.get_full_name() else user.username}

    return render(request, 'add_office.html', context)

# show and add
@csrf_exempt
def add_office_ajax(request):
    if request.method == 'POST':
        office_name = request.POST.get('office_name')
        abbreviation = request.POST.get('abbreviation')
        location = request.POST.get('location')

        if not office_name or not abbreviation or not location:
            return JsonResponse({'status': 'error', 'message': 'All fields are required'})

        else:
            office = Office.objects.create(office_name=office_name, abbreviation=abbreviation, location=location)
            return JsonResponse({'status': 'success', 'office_id': office.id})
        
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


def get_office(request, office_id):
    try:
        office = Office.objects.get(id=office_id)
        response_data = {
            "office_name": office.office_name,
            "abbreviation": office.abbreviation if office.abbreviation else "",
            "location": office.location if office.location else "",
            "created_at": localtime(office.created_at).strftime('%B %d, %Y, %I:%M %p')
        }
        return JsonResponse(response_data)

    except Office.DoesNotExist:
        return JsonResponse({"error": "Office not found"}, status=404)
    
# end of show and add

# delete
@csrf_exempt
def delete_office(request, office_id):
    if request.method == "DELETE":
        try:
            office = Office.objects.get(id=office_id)
            office.delete()
            return JsonResponse({"success": True})
        except Office.DoesNotExist:
            return JsonResponse({"success": False, "error": "Office not found"})
    return JsonResponse({"success": False, "error": "Invalid request method"})

# edit office
def update_office(request, office_id):
    if request.method == "POST":
        office = get_object_or_404(Office, id=office_id)

        office.office_name = request.POST.get("office_name", office.office_name)
        office.abbreviation = request.POST.get("abbreviation", office.abbreviation)
        office.location = request.POST.get("location", office.location)
        office.save()  # Automatically updates `updated_at`

        return JsonResponse({
            "success": True,
            "message": "Office updated successfully!",
            "updated_at": office.updated_at.strftime("%B %d, %Y, %I:%M %p")
        })

    return JsonResponse({"success": False, "message": "Invalid request!"}, status=400)



# for userlist


def list_users(request):
    user = request.user
    groups = Group.objects.all()
    users = User.objects.all().select_related("userprofile").order_by("id") # Fetch all users ordered by ID
    offices = Office.objects.all().order_by("id")  # Fetch all offices
   
    paginator = Paginator(users, 10)  # Show 10 users per page
    page_number = request.GET.get('page')  # Get the current page number
    page_obj = paginator.get_page(page_number)  # Get the paginated users

    context = {
        'page_obj': page_obj,  # Pass only the paginated object
        'display_name': user.get_full_name() if user.get_full_name() else user.username,
        'groups': groups,
        'offices': offices,

    }

    return render(request, "createuser.html", context)

# create user

def create_user(request):
    if request.method == "POST":
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        group_id = request.POST.get('group')  # Get the selected group ID from the form
        office_id = request.POST.get('office')  # Get the selected office ID from the form

        # Validate if passwords match
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('list_users')

        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('list_users')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already in use.")
            return redirect('list_users')

        # Create and save the new user
        user = User.objects.create_user(username=username, email=email, password=password)
        user.first_name = first_name
        user.last_name = last_name
        
        user.save()

        # Assign Group to user
        if group_id:
            try:
                group = Group.objects.filter(id__in=group_id)
                user.groups.set(group)
            except Group.DoesNotExist:
                messages.warning(request, "Group not found.")

        # Assign office using UserPermission
        if office_id:
            office = Office.objects.get(id=office_id)
            UserPermission.objects.create(user=user, office=office)

        messages.success(request, "User created successfully!")
        return redirect('list_users')

    return redirect('list_users')

# user changepassword and delete
@csrf_exempt
def change_password(request, user_id):
    if request.method == "POST":
        data = json.loads(request.body)
        new_password = data.get("password")

        user = get_object_or_404(User, id=user_id)
        user.set_password(new_password)
        user.save()

        return JsonResponse({"success": True, "message": "Password updated successfully!"})

    return JsonResponse({"success": False, "message": "Invalid request!"})

@csrf_exempt
def delete_user(request, user_id):
    if request.method == "DELETE":
        user = get_object_or_404(User, id=user_id)
        user.delete()

        return JsonResponse({"success": True, "message": "User deleted successfully!"})

    return JsonResponse({"success": False, "message": "Invalid request!"})

def update_user_access(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        selected_options = request.POST.getlist("access_options")  # Get selected checkboxes
        print(f"🔄 Updating access for user: {user.username}")
        print(f"✅ Selected permissions: {selected_options}")

        # Get or create user permission entry
        user_permission, created = UserPermission.objects.get_or_create(user=user)

        # Fetch the PermissionOption instances that match selected names
        valid_permissions = PermissionOption.objects.filter(name__in=selected_options)
        
        if not valid_permissions.exists():
            print("⚠️ Warning: No valid permissions found!")
        else:
            print(f"✅ Assigning Permissions: {list(valid_permissions.values_list('name', flat=True))}")

        # Clear previous permissions and set new ones
        user_permission.permissions.set(valid_permissions)
        user_permission.save()

        # Debugging: Verify the update
        updated_permissions = list(user_permission.permissions.values_list("name", flat=True))
        print(f"🔄 Updated permissions in DB: {updated_permissions}")

        return JsonResponse({"success": True, "message": "User access updated successfully!"})

    return JsonResponse({"success": False, "message": "Invalid request!"}, status=400)



def permission_required(access_option):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if access_option in request.session.get("user_permissions", []):
                return view_func(request, *args, **kwargs)
            return redirect("no_access")  # Redirect if unauthorized
        return _wrapped_view
    return decorator

def get_user_permissions(request, user_id):
    user = get_object_or_404(User, id=user_id)
    print(f"✅ Fetching permissions for user ID: {user_id} ({user.username})")

    # Get assigned permissions for the user
    user_permissions = list(
        UserPermission.objects.filter(user=user).values_list("permissions__name", flat=True)
    )

    # Get all available permissions
    all_permissions = list(PermissionOption.objects.values_list("name", flat=True))

    print(f"✅ User Permissions: {user_permissions}")
    print(f"✅ All Permissions: {all_permissions}")

    return JsonResponse({
        "user_permissions": user_permissions,
        "all_permissions": all_permissions
    })


@login_required
def service_request(request):
    user = request.user
    display_name = user.get_full_name() if user.get_full_name() else user.username
    status_choices = ServiceRequest.STATUS_CHOICES
    is_it = request.user.groups.filter(name='IT').exists()

    # 👇 Only users in IT group
    try:
        it_group = Group.objects.get(name="IT")
        it_users = it_group.user_set.all()
    except Group.DoesNotExist:
        it_users = []

    if request.method == "POST":
        service_category_id = request.POST.get("service_category")
        description = request.POST.get("description")
        assigned_to_id = request.POST.get("assigned_to")
        employee_name = request.POST.get("employee_name")
        employee_position = request.POST.get("employee_position")

        try:
            category = ServiceCategory.objects.get(id=service_category_id)
            assigned_to_user = User.objects.get(id=assigned_to_id)

            # ✅ Get user's office automatically
            try:
                user_permission = UserPermission.objects.get(user=user)
                office = user_permission.office
            except UserPermission.DoesNotExist:
                messages.error(request, "You don't have permission to submit a request.")
                return redirect("service_request")


            new_request = ServiceRequest.objects.create(
                service_category=category,
                office=office,
                description=description,
                requestor=user,
                assigned_to=assigned_to_user,
                submission_date=timezone.now(),
                status='Pending',
                employee_name=employee_name,
                employee_position=employee_position,
            )
        except (ServiceCategory.DoesNotExist, User.DoesNotExist):
            pass  # You may log this or handle it more gracefully

        # 🔔 Notify all IT users
        if new_request:
            # ✅ Figure out which page this request will appear on
            requests = ServiceRequest.objects.all().order_by('-submission_date')
            request_list = list(requests)
            index = request_list.index(new_request)
            page_number = ceil((index + 1) / 10)  # 10 per page, adjust if you change paginator

            # 1️⃣ Notify the assigned IT user first
            Notification.objects.create(
                recipient=assigned_to_user,
                message=f"You have been assigned a new request from {user.get_full_name() or user.username}",
                url=reverse("service_request") + f"?page={page_number}#row-{new_request.id}"
            )

            # 2️⃣ Notify the rest of the IT users
            for it_user in it_users.exclude(id=assigned_to_user.id):
                Notification.objects.create(
                    recipient=it_user,
                    message=f"New request submitted by {user.get_full_name() or user.username}",
                    url=reverse("service_request") + f"?page={page_number}#row-{new_request.id}"
                )


        return redirect('service_request')  # Redirect to avoid resubmission
    
    
    # Fetch service requests
    if user.groups.filter(name="IT").exists():
        service_requests = ServiceRequest.objects.all().order_by('-submission_date')
    else:
        service_requests = ServiceRequest.objects.filter(requestor=user).order_by('-submission_date')

    
    service_categories = ServiceCategory.objects.all()

    # ✅ Pagination
    paginator = Paginator(service_requests, 10)  # Show 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    elided_page_range = paginator.get_elided_page_range(number=page_obj.number)


    notifications = Notification.objects.filter(recipient=user, is_read=False)[:5]

    context = {
        "display_name": display_name,
        "page_obj": page_obj,  # 👈 Pass paginated service requests
        "service_requests": service_requests,
        "service_categories": service_categories,
        "users": it_users,  # 👈 Add this to pass IT users to template
        "status_choices": ServiceRequest.STATUS_CHOICES,
        'is_it': is_it,
        "notifications": notifications,
        "elided_page_range": elided_page_range,
    }

    return render(request, 'service_request.html', context)

@login_required
def mark_notification_read(request, notification_id):
    try:
        notif = Notification.objects.get(id=notification_id, recipient=request.user)
        notif.is_read = True
        notif.save(update_fields=["is_read"])  # ✅ make sure DB is updated
        return JsonResponse({"success": True})
    except Notification.DoesNotExist:
        return JsonResponse({"success": False})
    

@require_POST
@login_required
def change_status(request, request_id):
    service_request = get_object_or_404(ServiceRequest, id=request_id)

    # ✅ Check that the logged-in user is the assigned user
    if service_request.assigned_to != request.user:
        return HttpResponseForbidden("You are not authorized to change the status of this request.")

    new_status = request.POST.get("new_status")
    action_taken = request.POST.get("action_taken", "").strip()

    if new_status in dict(ServiceRequest.STATUS_CHOICES):
        service_request.status = new_status
        if new_status.lower() == 'completed':
            service_request.action_taken = action_taken
        else:
            service_request.action_taken = None  # Clear it

        print("Saving action taken:", action_taken)
        service_request.save()

    return redirect('service_request')


@require_POST
@login_required
def cancel_service_request(request, request_id):
    service_request = get_object_or_404(ServiceRequest, id=request_id)

    # ✅ Only requestor can cancel
    if service_request.requestor != request.user:
        return HttpResponseForbidden("You are not authorized to cancel this request.")

    # ✅ Only allow cancel if pending
    if service_request.status.lower() != "pending":
        messages.error(request, "Only pending requests can be canceled.")
        return redirect("service_request")

    service_request.status = "Cancelled"
    service_request.save()

    messages.success(request, f"Request #{service_request.id} has been cancelled.")
    return redirect("service_request")


# printing service request
def print_service_request(request, pk):
    try:
        sr = ServiceRequest.objects.get(pk=pk)
    except ServiceRequest.DoesNotExist:
        raise Http404("Service request not found")

    # Path to your PDF template
    template_path = os.path.join(settings.BASE_DIR, "Inventory_System/static/forms/FM-IT-001 Service Request.pdf")

    # Create a buffer for the overlay
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    # Normalization function for dash/spacing issues
    def normalize_text(text):
        text = unicodedata.normalize('NFKC', text)  # normalize Unicode
        text = text.replace("–", "-")  # en dash → hyphen
        text = text.replace("—", "-")  # em dash → hyphen
        return text.strip().lower()

    normalized_category = normalize_text(sr.service_category.name)

    # --- Category checkmark positions (Y-coordinate mapping) ---
    category_positions = {
        normalize_text("Repair of IT Equipment"): 606,
        normalize_text("Preventive Maintenance of IT Equipment"): 594,
        normalize_text("System Enhancement/Modification"): 581,
        normalize_text("Database Management and Administration (iHOMIS/iHOMIS+)"): 569,
        normalize_text("Network Installation"): 557,
        normalize_text("Internet Connections"): 545,
        normalize_text("Website Uploads"): 533,
        normalize_text("Technical Assistance"): 521,
        normalize_text("System Testing and Orientation"): 508,
        normalize_text("Training - iHOMIS Orientation/Computer Literacy"): 496,
        normalize_text("User Account Management"): 484,
        normalize_text("Others"): 472,
    }

    # --- Draw checkmark if matched ---
    if normalized_category in category_positions:
        can.setFont("Helvetica-Bold", 12)
        can.drawString(38, category_positions[normalized_category], "✓")

    # Helper function: wrap text by width
    def draw_wrapped_text(can, text, x, y, max_width, font_name="Helvetica", font_size=10, line_height=12, spacing_multiplier=1.0):
        can.setFont(font_name, font_size)
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if can.stringWidth(test_line, font_name, font_size) <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        # Apply spacing multiplier (e.g., 1.5 for 1.5 spacing)
        spacing = line_height * spacing_multiplier

        for i, line in enumerate(lines):
            can.drawString(x, y - (i * spacing), line)




    # --- Fill in text fields ---
    can.setFont("Helvetica", 10)
    can.drawString(465, 670, sr.submission_date.strftime("%m   %d    %Y"))
    draw_wrapped_text(can, sr.description, 290, 605, max_width=260, spacing_multiplier=1.3)
    can.drawString(80, 378, sr.employee_name if sr.employee_name else "Not specified")
    can.drawString(80, 342, sr.employee_position if sr.employee_position else "Not specified")
    can.drawString(165, 670, sr.office.office_name if sr.office else "")
    can.drawString(165, 655, sr.office.location or "—")
    can.drawString(400, 235, sr.assigned_to.get_full_name() if sr.assigned_to else "—")
    can.drawString(45, 235, sr.submission_date.strftime("%m/%d/%Y"))
    draw_wrapped_text(can, sr.action_taken or "No action taken", x=190, y=235, max_width=190, spacing_multiplier=1.3)
    can.drawString(325, 180, sr.submission_date.strftime("%m     %d    %Y"))
    can.drawString(80, 82, sr.employee_name if sr.employee_name else "Not specified")
    can.drawString(325, 82, sr.submission_date.strftime("%m     %d    %Y"))

    # Save overlay
    can.save()
    packet.seek(0)

    # Merge overlay with template PDF
    overlay_pdf = PdfReader(packet)
    existing_pdf = PdfReader(open(template_path, "rb"))
    output = PdfWriter()

    page = existing_pdf.pages[0]
    page.merge_page(overlay_pdf.pages[0])
    output.add_page(page)

    # Create final PDF in memory
    result_stream = io.BytesIO()
    output.write(result_stream)
    result_stream.seek(0)

    # Return the PDF
    return FileResponse(result_stream, as_attachment=False, filename=f"ServiceRequest_{sr.id}.pdf")

@login_required(login_url='/login/')
def encoding_error(request):
    user = request.user
    is_it = user.groups.filter(name="IT").exists()

    if request.method == "POST":
        # Extract form data
        date = request.POST.get("date")
        time = request.POST.get("time")
        area_section = request.POST.get("area_section")
        hospital_no = request.POST.get("hospital_no")
        patient_name = request.POST.get("patient_name")
        encoding_error_details = request.POST.get("encoding_error_details")
        correct_data_details = request.POST.get("correct_data_details")
        encoded_by = request.POST.get("encoded_by")
        encoded_date = request.POST.get("encoded_date")
        noted_by = request.POST.get("noted_by")
        noted_date = request.POST.get("noted_date")
        status = request.POST.get("status", "Pending")

        # Save to database
        request_obj = EncodingErrorRequest.objects.create(
            date=date,
            time=time,
            area_section=area_section,
            hospital_no=hospital_no,
            patient_name=patient_name,
            encoding_error_details=encoding_error_details,
            correct_data_details=correct_data_details,
            encoded_by=encoded_by,
            encoded_date=encoded_date if encoded_date else None,
            noted_by=noted_by if noted_by else None,
            noted_date=noted_date if noted_date else None,

            # ✅ Always set verified by
            verified_by="Joselito Esteban A. Biscocho",
            verified_date=timezone.now().date(),  # auto-stamp the date

            status=status,
        )

        # ✅ Figure out the page for highlight/scroll animation
        requests = EncodingErrorRequest.objects.all().order_by("-created_at")
        request_list = list(requests)
        index = request_list.index(request_obj)
        page_number = ceil((index + 1) / 10)  # 10 per page

        url = reverse("encoding_error") + f"?page={page_number}#row-{request_obj.id}"

        # 🔔 Notify all IT members
        it_group = Group.objects.get(name="IT")
        for it_user in it_group.user_set.all():
            Notification.objects.create(
                recipient=it_user,
                message=f"New Encoding Error request submitted by {user.username} (Patient: {patient_name})",
                url=reverse("encoding_error") + f"?page={page_number}&from=notif#row-{request_obj.id}"
            )

        messages.success(request, "Encoding Error Request added successfully!")
        return redirect(url)

    # GET: show list with pagination
    encoding_list = EncodingErrorRequest.objects.all().order_by("-created_at")
    paginator = Paginator(encoding_list, 10)  # 10 records per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)  # alias for template
    encoding_requests = page_obj

    context = {
        "encoding_requests": encoding_requests,
        "page_obj": page_obj,
        "is_it": is_it,
    }
    
    return render(request, "encoding_error.html", context)

@login_required(login_url='/login/')
def change_encoding_status(request):
    if request.method == "POST":
        request_id = request.POST.get("request_id")
        new_status = request.POST.get("status")

        encoding_request = get_object_or_404(EncodingErrorRequest, id=request_id)
        encoding_request.status = new_status

        # If IT marks as Completed → set corrected_by & corrected_date
        if new_status == "Completed" and request.user.groups.filter(name="IT").exists():
            encoding_request.corrected_by = request.user   # save the actual User instance
            encoding_request.corrected_date = timezone.now().date()  # just date since it's DateField

            # Also set verified_date to match corrected_date
            encoding_request.verified_date = encoding_request.corrected_date

        encoding_request.save()
        messages.success(request, f"Request status updated to {new_status}.")
        return redirect("encoding_error")

@login_required(login_url='/login/')
def edit_encoding_error(request):
    if request.method == "POST":
        request_id = request.POST.get("request_id")
        try:
            encoding_request = EncodingErrorRequest.objects.get(id=request_id)
        except EncodingErrorRequest.DoesNotExist:
            messages.error(request, "Request not found.")
            return redirect("encoding_error")

        # Update fields
        encoding_request.date = request.POST.get("date")
        encoding_request.time = request.POST.get("time")
        encoding_request.area_section = request.POST.get("area_section")
        encoding_request.hospital_no = request.POST.get("hospital_no")
        encoding_request.patient_name = request.POST.get("patient_name")
        encoding_request.encoding_error_details = request.POST.get("encoding_error_details")
        encoding_request.correct_data_details = request.POST.get("correct_data_details")
        encoding_request.encoded_by = request.POST.get("encoded_by")
        encoding_request.encoded_date = request.POST.get("encoded_date") or None

        encoding_request.noted_by = request.POST.get("noted_by")
        encoding_request.noted_date = request.POST.get("noted_date") or None

        encoding_request.save()

        messages.success(request, "Encoding Error Request updated successfully!")
        return redirect("encoding_error")

# printing encoding error request
@login_required(login_url='/login/')
def print_encoding_error(request, pk):
    try:
        er = EncodingErrorRequest.objects.get(pk=pk)
    except EncodingErrorRequest.DoesNotExist:
        raise Http404("Encoding error request not found")

    # Path to your Encoding Error PDF template
    template_path = os.path.join(settings.BASE_DIR, "Inventory_System/static/forms/FM-IT-005 Encoding Error.pdf")

    # Create a buffer for the overlay
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    # --- Fill in text fields ---
    can.setFont("Helvetica", 10)

    # Adjust coordinates to match your FM-IT-005 layout
    # (you will need to test-print and tweak these values)
    can.drawString(65, 580, er.date.strftime("%m    %d    %Y") if er.date else "")
    can.drawString(183, 580, er.time.strftime("%I:%M %p") if er.time else "")
    can.drawString(334, 580, er.area_section or "")
    can.drawString(95, 549, er.hospital_no or "")
    can.drawString(115, 536, er.patient_name or "")

    # Error details (wrapped text)
    def draw_wrapped_text(can, text, x, y, max_width, font_name="Helvetica", font_size=10, line_height=12, spacing_multiplier=1.0):
        can.setFont(font_name, font_size)
        words = text.split()
        lines, current_line = [], ""
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if can.stringWidth(test_line, font_name, font_size) <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        spacing = line_height * spacing_multiplier
        for i, line in enumerate(lines):
            can.drawString(x, y - (i * spacing), line)

    draw_wrapped_text(can, er.encoding_error_details or "", 70, 495, max_width=450, spacing_multiplier=1.1)
    draw_wrapped_text(can, er.correct_data_details or "", 70, 402, max_width=450, spacing_multiplier=1.1)

    # Encoded by
    can.drawString(95, 317, er.encoded_by or "")
    can.drawString(277, 317, er.encoded_date.strftime("%m   %d   %Y") if er.encoded_date else "")

    # Noted by
    can.drawString(95, 269, er.noted_by or "")
    can.drawString(279, 269, er.noted_date.strftime("%m   %d   %Y") if er.noted_date else "")

    # Corrected by (IT)
    corrected_name = er.corrected_by.get_full_name() if er.corrected_by else ""
    corrected_date_str = er.corrected_date.strftime("%m   %d   %Y") if er.corrected_date else ""

    can.drawString(95, 138, corrected_name)      # Adjust X, Y coordinates to fit your PDF layout
    can.drawString(165, 200, corrected_date_str)

    # Verified by (always Joselito, fixed)
    can.drawString(362, 138, "Joselito Esteban A. Biscocho")

    verified_date_str = er.verified_date.strftime("%m   %d   %Y") if er.verified_date else ""
    can.drawString(462, 200, verified_date_str)  # Adjust coordinates to fit your template

    # Save overlay
    can.save()
    packet.seek(0)

    # Merge overlay with template PDF
    overlay_pdf = PdfReader(packet)
    existing_pdf = PdfReader(open(template_path, "rb"))
    output = PdfWriter()

    page = existing_pdf.pages[0]
    page.merge_page(overlay_pdf.pages[0])
    output.add_page(page)

    # Create final PDF in memory
    result_stream = io.BytesIO()
    output.write(result_stream)
    result_stream.seek(0)

    # Return the PDF
    return FileResponse(result_stream, as_attachment=False, filename=f"EncodingError_{er.id}.pdf")


@login_required
def web_uploading(request):
    requests_qs = WebsiteUploadRequest.objects.all().order_by("-date", "-id")

    # Apply pagination (10 per page, you can change to 20/50 if needed)
    paginator = Paginator(requests_qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    if request.method == "POST":
        form = WebsiteUploadRequestForm(request.POST, request.FILES)
        files = request.FILES.getlist("file")  # multiple uploads

        if form.is_valid():
            upload_request = form.save(commit=False)
            upload_request.user = request.user

            # If prepared_date is not manually entered, default to "date"
            if not upload_request.prepared_date:
                upload_request.prepared_date = upload_request.date  

            upload_request.save()

            # Save attachments
            for f in files:
                WebsiteUploadAttachment.objects.create(request=upload_request, file=f)

            # ✅ Figure out which page the new request is on
            all_requests = WebsiteUploadRequest.objects.all().order_by("-date")
            request_list = list(all_requests)
            index = request_list.index(upload_request)
            page_number = ceil((index + 1) / 10)  # 10 per page

            url = reverse("web_uploading") + f"?page={page_number}#row-{upload_request.id}"

            # (Optional) You can also notify IT group here like encoding_error
            # 🔔 Notify all IT users
            it_users = Group.objects.get(name="IT").user_set.all()
            for it_user in it_users:
                Notification.objects.create(
                    recipient=it_user,
                    message=f"New Website Upload Request submitted by {request.user.get_full_name() or request.user.username}",
                    url=reverse("web_uploading") + f"?page={page_number}&from=notif#row-{upload_request.id}"
                )

            return redirect(url)
    else:
        form = WebsiteUploadRequestForm()

    context = {
        "is_it": request.user.groups.filter(name="IT").exists(),
        "requests": page_obj,
        "form": form,
        "paginator": paginator,
    }

    return render(request, "web_uploading.html", context)

@login_required
def web_upload_detail(request, pk):
    req = get_object_or_404(WebsiteUploadRequest, pk=pk)
    return render(request, "web_upload_detail.html", {"req": req})

@login_required
def web_upload_edit(request, pk):
    request_obj = get_object_or_404(WebsiteUploadRequest, pk=pk)

    if request.method == 'POST':
        form = WebsiteUploadRequestForm(request.POST, request.FILES, instance=request_obj)
        if form.is_valid():
            form.save()

            # 1️⃣ Remove any attachments the user marked for deletion
            remove_ids = request.POST.getlist('remove_files')
            if remove_ids:
                request_obj.attachments.filter(id__in=remove_ids).delete()

            # 2️⃣ Save new uploaded attachments
            for f in request.FILES.getlist('new_files'):
                request_obj.attachments.create(file=f)

            return redirect('web_uploading')  # back to list page
    else:
        # GET: just redirect back, since edit happens via modal
        return redirect('web_uploading')

@login_required
def web_upload_delete(request, pk):
    req = get_object_or_404(WebsiteUploadRequest, pk=pk)
    req.delete()
    return redirect("web_uploading")


@login_required
def web_upload_receive(request, pk):
    req = get_object_or_404(WebsiteUploadRequest, pk=pk)

    # Only IT group can mark as received
    if not request.user.groups.filter(name="IT").exists():
        return redirect("web_uploading")

    # Mark as received
    req.received_by = request.user.get_full_name() or request.user.username
    req.received_date = timezone.now()
    req.save()

    # Notify requester
    Notification.objects.create(
        recipient=req.user,
        message = f"Your Latest Website Upload Request has been marked as received by {req.received_by}.",
        url=reverse("web_uploading") + f"#row-{req.id}"
    )

    return redirect("web_uploading")

@login_required(login_url='/login/')
def print_web_upload_request(request, pk):
    try:
        req = WebsiteUploadRequest.objects.get(pk=pk)
    except WebsiteUploadRequest.DoesNotExist:
        raise Http404("Website Upload Request not found")

    # Path to FM-IT-004 Web Upload PDF template
    template_path = os.path.join(
        settings.BASE_DIR,
        "Inventory_System/static/forms/FM-IT-004 Web Upload.pdf"
    )

    # Create overlay
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont("Helvetica", 10)

    # --- Helper function for wrapping long text ---
    def draw_wrapped_text(can, text, x, y, max_width, font_name="Helvetica", font_size=10, line_height=12, spacing_multiplier=1.0):
        can.setFont(font_name, font_size)
        words = text.split()
        lines, current_line = [], ""
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if can.stringWidth(test_line, font_name, font_size) <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        spacing = line_height * spacing_multiplier
        for i, line in enumerate(lines):
            can.drawString(x, y - (i * spacing), line)


    # --- Fill in request fields (adjust coordinates to match FM-IT-004 layout) ---

    prepared_date = req.prepared_date or req.date
    # this is for the Date Reqquested at top left
    can.drawString(69, 543, prepared_date.strftime("%m   %d   %Y") if prepared_date else "")

    can.drawString(325, 543, req.area_section or "")
    draw_wrapped_text(can, req.details_of_request or "", 70, 497, max_width=480, spacing_multiplier=1.3)

    if req.attachments.exists():   # works if you use a related_name="attachments"
    # Adjust the coordinates (x, y) so the checkmark falls inside the box
        can.drawString(83, 197, "✔")

    can.drawString(102, 111, req.prepared_by or "")
    # this is for the Date Prepared at lower left
    can.drawString(216, 173, prepared_date.strftime("%m  %d  %Y") if prepared_date else "")

    if req.received_by:
        can.drawString(375, 111, req.received_by or "")
        can.drawString(490, 173, req.received_date.strftime("%m  %d  %Y") if req.received_date else "")

    # Save overlay
    can.save()
    packet.seek(0)

    # Merge overlay with template
    overlay_pdf = PdfReader(packet)
    existing_pdf = PdfReader(open(template_path, "rb"))
    output = PdfWriter()

    page = existing_pdf.pages[0]
    page.merge_page(overlay_pdf.pages[0])
    output.add_page(page)

    result_stream = io.BytesIO()
    output.write(result_stream)
    result_stream.seek(0)

    return FileResponse(result_stream, as_attachment=False, filename=f"WebUpload_{req.id}.pdf")


#Reports starts here
def service_request_report(request):
    # Default: today
    today = now().date()
    selected_date = request.GET.get("date")

    if selected_date:
        try:
            today = datetime.strptime(selected_date, "%Y-%m-%d").date()
        except ValueError:
            pass  # fallback to today's date if parsing fails

    service_requests = ServiceRequest.objects.filter(
        submission_date__date=today
    ).order_by("submission_date")

    return render(request, "reports/service_request/service_request_report.html", {
        "service_requests": service_requests,
        "today": today,
    })

@login_required
def service_request_monthly_report(request):
    # Default: current month
    today = now()
    month = today.month
    year = today.year

    # If user chose a month from the modal (format: YYYY-MM)
    selected_month = request.GET.get("month")
    if selected_month:
        try:
            year, month = map(int, selected_month.split("-"))
        except ValueError:
            pass  # fallback to current month if parsing fails

    # First and last day of selected month
    first_day = datetime(year, month, 1)
    if month == 12:
        last_day = datetime(year + 1, 1, 1)
    else:
        last_day = datetime(year, month + 1, 1)

    # Query service requests for that month
    service_requests = ServiceRequest.objects.filter(
        submission_date__date__gte=first_day,
        submission_date__date__lt=last_day
    ).order_by("submission_date")

    return render(request, "reports/service_request/service_request_monthly_report.html", {
        "service_requests": service_requests,
        "generated_date": today,
        "month_name": first_day.strftime("%B %Y"),  # example: August 2025
    })

@login_required
def service_request_custom_report(request):
    # Default: today
    today = now().date()
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")

    start_date = end_date = today

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass  # fallback to today if parsing fails

    service_requests = ServiceRequest.objects.filter(
        submission_date__date__gte=start_date,
        submission_date__date__lte=end_date
    ).order_by("submission_date")

    return render(request, "reports/service_request/service_request_custom_report.html", {
        "service_requests": service_requests,
        "start_date": start_date,
        "end_date": end_date,
        "date_range_name": f"{start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}",
    })