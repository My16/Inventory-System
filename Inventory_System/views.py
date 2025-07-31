from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Office
from .forms import OfficeForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.shortcuts import get_object_or_404
from django.utils.timezone import localtime
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from functools import wraps
from .models import UserPermission, PermissionOption

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



@login_required(login_url='/login/')
def homepage(request):
    user = request.user
    user_permissions = request.session.get("user_permissions", [])

    display_name = user.get_full_name() if user.get_full_name() else user.username

    context = {"display_name": display_name, "useer_permissions": user_permissions}

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
    users = User.objects.all().order_by("id")  # Fetch all users ordered by ID

    paginator = Paginator(users, 14)  # Show 14 users per page
    page_number = request.GET.get('page')  # Get the current page number
    page_obj = paginator.get_page(page_number)  # Get the paginated users

    context = {
        'page_obj': page_obj,  # Pass only the paginated object
        'display_name': user.get_full_name() if user.get_full_name() else user.username
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


def service_request(request):
    user = request.user
    display_name = user.get_full_name() if user.get_full_name() else user.username

    context = {"display_name": display_name}
    return render(request, 'service_request.html', context)