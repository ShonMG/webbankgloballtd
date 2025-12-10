from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ProfileForm
from .models import Profile

@login_required
def create_profile(request):
    if hasattr(request.user, 'profile'):
        return redirect('dashboard:main_dashboard')

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            return redirect('application_submitted')
    else:
        form = ProfileForm()

    return render(request, 'profiles/create_profile.html', {'form': form})

def application_submitted(request):
    return render(request, 'profiles/application_submitted.html')