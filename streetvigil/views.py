import json
from django.http import HttpResponse, HttpResponseRedirect , JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.db import IntegrityError
import folium
from folium import plugins
from django.db.models import Q
from .forms import CapturedImageForm
from .models import *
from .models import CapturedImage
import json

def index(request):
    context = {}
    if request.user.is_authenticated:
        user_reports = CapturedImage.objects.filter(reported_by=request.user)
        total_reports = user_reports.count()
        total_points = request.user.points

        context = {
            'total_reports': total_reports,
            'total_points': total_points,
            'user_reports': user_reports,  # If you want to display user's reports in the template
        }
    return render(request, 'index.html', context)

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        # firstname = request.POST["firstname"]
        # lastname = request.POST["lastname"]
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            # user = User.objects.create_user(email, firstname, lastname)
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "register.html")

# def capture_image(request):
#     if request.method == 'POST':
#         form = CapturedImageForm(request.POST, request.FILES)
#         if form.is_valid():
#             instance = form.save()
#             return JsonResponse({'message': 'Image saved successfully', 'image_url': instance.image.url})
#         else:
#             return JsonResponse({'error': 'Form errors', 'errors': form.errors})
#     else:
#         form = CapturedImageForm()

#     return render(request, 'capture_image.html', {'form': form})

def capture(request):
    if request.method == 'POST':
        form = CapturedImageForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)
            category = request.POST['category']
            lat =  request.POST['latitude']
            lon = request.POST['longitude']

            instance.category = category
            instance.latitude = lat 
            instance.longitude = lon
            print(category , lat , lon)
            instance.save()

            return JsonResponse({'message': 'Image saved successfully', 'image_url': instance.image.url})
        else:
            return JsonResponse({'error': 'Form errors', 'errors': form.errors})
    else:
        form = CapturedImageForm()

    return render(request, 'capture.html', {'form': form})





# def capture(request):
#     if request.method == 'POST':
#         # Handle the image file separately from the form
#         image_form = CapturedImageForm(request.POST, request.FILES)
        
#         # Check if the image form is valid
#         if image_form.is_valid():
#             # Save the image form to get the instance
#             image_instance = image_form.save(commit=False)

#             # Now handle the additional fields
#             category = request.POST.get('category')
#             description = request.POST.get('description')
#             reported_by = request.POST.get('reported_by')
#             location = request.POST.get('location')

#             # Assign the additional fields to the image instance
#             image_instance.category = category
#             image_instance.description = description
#             image_instance.reported_by = reported_by
#             image_instance.location = location

#             # Save the image instance with the additional fields
#             image_instance.save()

#             # Return a JsonResponse with success message and image URL
#             return JsonResponse({'message': 'Image and data saved successfully', 'image_url': image_instance.image.url})
#         else:
#             # Return a JsonResponse with form errors if the image form is not valid
#             return JsonResponse({'error': 'Form errors', 'errors': image_form.errors})
#     else:
#         # Create a new instance of the image form for rendering the initial form
#         image_form = CapturedImageForm()

#     # Render the form in case of a GET request or form validation errors
#     return render(request, 'capture.html', {'image_form': image_form})



def upload(request):
    if request.method == 'POST':
        form = CapturedImageForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save()
            request.session['captured_image_instance'] = instance.id
            return redirect('report_interface')
        else:
            return JsonResponse({'error': 'Form errors', 'errors': form.errors})
    else:
        form = CapturedImageForm()
    return render(request, 'upload.html', {'form': form})

def report_interface(request):
    instance_id = request.session.get('captured_image_instance')

    if not instance_id:
        return redirect('upload')

    instance = get_object_or_404(CapturedImage, id=instance_id)

    form = CapturedImageForm(instance=instance)
    return render(request, 'report_interface.html', {'form': form})

def report_submission_view(request):
    instance_id = request.session.get('captured_image_instance')

    if not instance_id:
        return redirect('upload')

    instance = get_object_or_404(CapturedImage, id=instance_id)

    if request.method == 'POST':
        category = request.POST.get('category')
        description = request.POST.get('description')

        new_instance = CapturedImage.objects.create(
            image=instance.image,
            category=category,
            description=description,
            reported_by=request.user,
            latitude=instance.latitude,
            longitude=instance.longitude,
            verified=False,
            rewards=0,
            created_at=timezone.now()
        )

        del request.session['captured_image_instance']

        return redirect('success_page')

    form = CapturedImageForm(instance=instance)
    return render(request, 'report_interface.html', {'form': form})

def success_page(request):
    return render(request, 'success_page.html')

def all_images(request):
    images = CapturedImage.objects.all()
    return render(request, 'all_images.html', {'images': images})

def report_interface(request):
    # Assuming you have the instance_id saved in the session during the upload view
    instance_id = request.session.get('captured_image_instance')

    if not instance_id:
        # Redirect to upload page if instance_id is not found in the session
        return redirect('upload')

    # Retrieve the CapturedImage instance from the database
    instance = get_object_or_404(CapturedImage, id=instance_id)

    form = CapturedImageForm(instance=instance)
    return render(request, 'report_interface.html', {'form': form})


def police(request):
    crime_data_objects = CapturedImage.objects.filter(verified=False)

    context = {
        'crime_data_objects': crime_data_objects,
    }
    return render(request, 'police_dashboard/policed.html', context)

def crime_report(request, crime_id):
    crime_event = get_object_or_404(CapturedImage, id=crime_id)

    # Create Folium map and add marker for crime location
    crime_map = folium.Map(location=[crime_event.latitude, crime_event.longitude], zoom_start=13)
    folium.Marker([crime_event.latitude, crime_event.longitude],
                  popup=f"Category: {crime_event.category}, Description: {crime_event.description}",
                  icon=folium.Icon(color='red', icon='circle', prefix='fa')).add_to(crime_map)

    # Save the map as an HTML string
    crime_map_html = crime_map._repr_html_()

    context = {
        'crime_event': crime_event,
        'crime_map_html': crime_map_html,  # Pass the map as HTML string
    }

    return render(request, 'police_dashboard/crime_report.html', context)

# def police(request):
#     latitude = 17.60004477572919
#     longitude = 78.41767026216672

#     my_map = folium.Map(location=[latitude, longitude], zoom_start=13)

#     # Add a marker for the initial location
#     user_icon = folium.Icon(color='blue', icon='user', prefix='fa')
#     folium.Marker([latitude, longitude], popup='Your Location', icon=user_icon).add_to(my_map)

#     crime_data_objects = CapturedImage.objects.filter(verified=False)

#     crime_data = [
#         {'latitude': 17.592192076250978, 'longitude': 78.408226580168, 'category': 'Theft', 'description': 'Stolen item'},
#         {'latitude': 17.601, 'longitude': 78.42, 'category': 'Accident', 'description': 'Car accident'},
#         # Add more crime data as needed,
#     ]

#     # Iterate over crime data and add markers to the map with the correct icon
#     for crime_point in crime_data_objects:
#         icon = folium.Icon(color='red', icon='circle', prefix='fa')
#         folium.Marker([crime_point.latitude, crime_point.longitude], 
#                     popup=f"Category: {crime_point.get_category_display()}, Description: {crime_point.description}",
#                     icon=icon).add_to(my_map)
#     context = {
#         'map': my_map._repr_html_(),
#         'latitude': latitude,
#         'longitude': longitude,
#         'other_data': 'Your additional data',
#     }

#     return render(request, 'police_dashboard/police.html', context)

