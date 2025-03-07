from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

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

def homepage(request):
    user = request.user

    display_name = user.get_full_name() if user.get_full_name() else user.username

    context = {"display_name": display_name}

    return render(request, 'home.html', context)