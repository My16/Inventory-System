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
            return redirect('homepage')  # Redirect to dashboard
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('loginpage') # Redirect to loginpage
    
    context = {}

    return render(request, 'loginPage.html', context)

@login_required(login_url='/login/')
def homepage(request):
    user = request.user

    display_name = user.get_full_name() if user.get_full_name() else user.username

    context = {"display_name": display_name}

    return render(request, 'home.html', context)

@login_required(login_url='/login/')
def add_office(request):
    user = request.user
    offices = Office.objects.all().order_by("id")  # Ascending order

    paginator = Paginator(offices, 14) #show 20 offices per page

    page_number = request.GET.get('page') #Get the current page number
    page_obj = paginator.get_page(page_number) #Get the page object

    context = {'offices': offices, 'display_name': user.get_full_name() if user.get_full_name() else user.username}
    return render(request, 'add_office.html', {'page_obj': page_obj})

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