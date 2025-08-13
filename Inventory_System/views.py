from urllib import request
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Office, ServiceRequest, ServiceCategory
from .forms import OfficeForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json, random, colorsys, io, os, unicodedata
from django.shortcuts import get_object_or_404
from django.utils.timezone import localtime
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
from django.utils.timezone import now
from django.db.models import Count
from django.db.models.functions import TruncDate
from collections import defaultdict
from collections import defaultdict
from django.http import FileResponse, Http404
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter

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

@login_required(login_url='/login/')
def homepage(request):
    user = request.user
    user_permissions = request.session.get("user_permissions", [])
    is_it = user.groups.filter(name='IT').exists()
    display_name = user.get_full_name() if user.get_full_name() else user.username

    # Total number of service requests
    total_requests = ServiceRequest.objects.count()

    # Total number of service requests today
    today = now().date()
    total_requests_today = ServiceRequest.objects.filter(submission_date__date=today).count()

    # Requests assigned to current IT user
    assigned_to_user = ServiceRequest.objects.filter(assigned_to=user)
    assigned_count = assigned_to_user.count()

    # Completed requests by current IT user
    completed_by_user = assigned_to_user.filter(status='Completed').count()

    # Group by assigned IT personnel and date
    completed_by_it_and_date = (
        ServiceRequest.objects
        .filter(status='Completed')
        .annotate(date=TruncDate('submission_date'))
        .values('assigned_to__username', 'date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    # Data for bar chart (total requests per office)
    requests_per_office = (
        ServiceRequest.objects
        .values('office__abbreviation')
        .annotate(total=Count('id'))
        .order_by('-total')  # Optional: sort by most requests first
    )

    # Format data
    chart_dict = defaultdict(lambda: defaultdict(int))
    dates_set = set()

    for entry in completed_by_it_and_date:
        username = entry['assigned_to__username']
        date = entry['date'].strftime('%Y-%m-%d')
        chart_dict[username][date] = entry['count']
        dates_set.add(date)

    sorted_dates = sorted(list(dates_set))

    line_chart_datasets = []
    for username, counts in chart_dict.items():
        data = [counts.get(date, 0) for date in sorted_dates]
        line_chart_datasets.append({
            'label': username,
            'data': data,
        })

    # Format bar chart data
    bar_chart_labels = [
    entry['office__abbreviation'] or entry['office__office_name'][:3].upper() 
    for entry in requests_per_office
    ]
    bar_chart_data = [entry['total'] for entry in requests_per_office]
    bar_chart_colors = generate_distinct_colors(len(bar_chart_labels))

    context = {
        'total_requests': total_requests,
        'total_requests_today': total_requests_today,
        'assigned_count': assigned_count,
        'completed_by_user': completed_by_user,
        "display_name": display_name,
        "user_permissions": user_permissions,
        'line_chart_labels': sorted_dates,
        'line_chart_datasets': line_chart_datasets,
        'bar_chart_labels': bar_chart_labels,
        'bar_chart_data': bar_chart_data,
        'bar_chart_colors': bar_chart_colors,
        'is_it': is_it,
    }

    return render(request, 'home.html', context)

@login_required(login_url='/login/')
def add_office(request):
    user = request.user
    offices = Office.objects.all().order_by("id")  # Ascending order

    paginator = Paginator(offices, 14) #show 20 offices per page

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
    users = User.objects.all().order_by("id")  # Fetch all users ordered by ID
    offices = Office.objects.all().order_by("id")  # Fetch all offices

    paginator = Paginator(users, 14)  # Show 14 users per page
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

    if request.method == "POST":
        service_category_id = request.POST.get("service_category")
        description = request.POST.get("description")
        assigned_to_id = request.POST.get("assigned_to")

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


            ServiceRequest.objects.create(
                service_category=category,
                office=office,
                description=description,
                requestor=user,
                assigned_to=assigned_to_user,
                submission_date=timezone.now(),
                status='Pending',
            )
        except (ServiceCategory.DoesNotExist, User.DoesNotExist):
            pass  # You may log this or handle it more gracefully

        return redirect('service_request')  # Redirect to avoid resubmission
    
    # Fetch service requests
    if user.groups.filter(name="IT").exists():
        service_requests = ServiceRequest.objects.all().order_by('-submission_date')
    else:
        service_requests = ServiceRequest.objects.filter(requestor=user).order_by('-submission_date')

    
    service_categories = ServiceCategory.objects.all()

    # ✅ Pagination
    paginator = Paginator(service_requests, 6)  # Show 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 👇 Only users in IT group
    try:
        it_group = Group.objects.get(name="IT")
        it_users = it_group.user_set.all()
    except Group.DoesNotExist:
        it_users = []

    context = {
        "display_name": display_name,
        "page_obj": page_obj,  # 👈 Pass paginated service requests
        "service_requests": service_requests,
        "service_categories": service_categories,
        "users": it_users,  # 👈 Add this to pass IT users to template
        "status_choices": ServiceRequest.STATUS_CHOICES,
        'is_it': is_it,
    }

    return render(request, 'service_request.html', context)

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
    template_path = os.path.join(settings.BASE_DIR, "Inventory_System/static/forms/Service Request.pdf")

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
    can.drawString(165, 670, sr.requestor.get_full_name())
    can.drawString(165, 655, sr.office.location or "—")
    can.drawString(400, 235, sr.assigned_to.get_full_name() if sr.assigned_to else "—")
    can.drawString(45, 235, sr.submission_date.strftime("%m/%d/%Y"))
    draw_wrapped_text(can, sr.action_taken or "No action taken", x=190, y=235, max_width=190, spacing_multiplier=1.3)
    can.drawString(325, 180, sr.submission_date.strftime("%m     %d    %Y"))
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