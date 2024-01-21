from django.http import HttpResponse, HttpResponseRedirect , JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
import pytesseract
from folium import plugins
from django.db.models import Q, Sum
from .forms import CapturedImageForm
from .models import *
from .models import CapturedImage
import json, requests, cv2, folium
import numpy as np

def index(request):
    context = {}
    if request.user.is_authenticated  and request.user.username!= 'admin'  :
        user_reports = CapturedImage.objects.filter(reported_by=request.user)

        pending = user_reports.filter(status='P')
        approved = user_reports.filter(status='A')
        rejected = user_reports.filter(status='R')

        total_rewards = approved.aggregate(Sum('rewards'))['rewards__sum']
        total_rewards = total_rewards if total_rewards is not None else 0

        total_submissions = approved.count() + rejected.count()

        context = {
            'total_rewards': total_rewards,
            'total_submissions': total_submissions,
            'pending_no': pending.count(),
            'approved_no': approved.count(),
            'rejected_no': rejected.count(),

            'pending': pending,
            'approved': approved,
            'rejected': rejected
        }

    elif request.user.username == 'admin':

        pending = CapturedImage.objects.filter(status='P')
        approved = CapturedImage.objects.filter(status='A')
        rejected = CapturedImage.objects.filter(status='R')

        total_rewards = approved.aggregate(Sum('rewards'))['rewards__sum']
        total_rewards = total_rewards if total_rewards is not None else 0

        total_submissions = approved.count() + rejected.count()

        context = {
            'pending_no': pending.count(),
            'approved_no': approved.count(),
            'rejected_no': rejected.count(),

            'pending': pending,
            'approved': approved,
            'rejected': rejected,
        }

    return render(request, 'index.html', context)

def login_view(request):
    if request.method == "POST":

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
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirmation = request.POST.get("confirmation")
        if password != confirmation:
            return render(request, "register.html", {
                "message": "Passwords must match."
            })

        try:
            user = User.objects.create_user(username, email, password)
            print("data saveing")
            user.save()
        except IntegrityError:
            return render(request, "register.html", {
                "message": "Username already taken."
            })
        print("doneee")
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "register.html")

def capture(request):
    if request.method == 'POST':
        print('POST request data:', request.POST)

        form = CapturedImageForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)

            instance.save()
            # return render(request , 'aftercapture.html', {'form' : form})
            return JsonResponse({'message': 'Image saved successfully', 'redirect_url': '/streetvigil/aftercapture'})
        else:
            return JsonResponse({'error': 'Form errors', 'errors': form.errors})
    else:
        form = CapturedImageForm()

    return render(request, 'capture.html', {'form': form})

from django.shortcuts import render, redirect

def aftercapture(request):
    if request.method == 'POST':
        # Get the latest CapturedImage instance
        last_obj = CapturedImage.objects.latest('created_at')

        # Update fields based on the form data
        last_obj.category = request.POST.get('category')
        last_obj.description = request.POST.get('description')
        last_obj.reported_by =request.user
        last_obj.latitude = request.POST.get('latitude')
        last_obj.longitude = request.POST.get('longitude')

        # Save the changes
        last_obj.save()

        # Redirect to a success page or render a response as needed
        return redirect('success_page')  # Replace 'success_page' with the actual URL or view name

    else:
        # If it's not a POST request, render the initial aftercapture.html template
        last_obj = CapturedImage.objects.latest('created_at')
        return render(request, 'aftercapture.html', {'image_url': last_obj.image.url})

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
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        new_instance = CapturedImage.objects.create(
            image=instance.image,
            category=category,
            description=description,
            reported_by=request.user,
            latitude=latitude,
            longitude=longitude,
            verified=False,
            rewards=0,
            created_at=timezone.now()
        )

        # delete previous instance here
        

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

def detect_and_ocr_license_plate(image_path):
    # Load the image
    img = cv2.imread(image_path)

    # Convert the image to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply a blur to reduce noise and improve edge detection
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Apply edge detection using Canny
    edges = cv2.Canny(blurred, 50, 150)

    save_path = f'plate_roi_before_ocr.jpg'
    cv2.imwrite(save_path, edges)
    print(f'Image before OCR saved at: {save_path}')

    # Find contours in the edged image
    contours, _ = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter contours based on area (adjust the area threshold as needed)
    min_area_threshold = 500
    valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area_threshold]

    # Iterate over the valid contours
    for contour in valid_contours:
        # Approximate the contour as a polygon
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        # If the polygon has four vertices, it may be a license plate
        if len(approx) == 4:
            # Draw a rectangle around the license plate
            x, y, w, h = cv2.boundingRect(approx)
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Extract the region of interest (ROI) containing the potential license plate
            plate_roi = gray[y:y + h, x:x + w]

            # Perform OCR on the potential license plate ROI using Tesseract
            plate_number = perform_ocr(plate_roi)

            return plate_number

    return None

def perform_ocr(plate_roi):
    # Perform OCR using Tesseract
    # custom_config = r'--oem 3 --psm 6 outputbase digits'
    custom_config = r'--oem 3 --psm 6 outputbase alphanumeric'
    plate_number = pytesseract.image_to_string(plate_roi, config=custom_config).strip()

    return plate_number

def police(request):
    crime_data_objects = CapturedImage.objects.filter(verified=False)

    context = {
        'crime_data_objects': crime_data_objects,
    }
    return render(request, 'police_dashboard/policed.html', context)

def crime_report(request, crime_id):
    if request.method == "POST" :
        obj =  CapturedImage.objects.get(id =  crime_id)
        actionType = request.POST.get('action')
        print('action type is ',actionType)
        if(actionType == 'accept') :
            rewards = request.POST.get('creditRupees')
            obj.rewards = rewards
            obj.status = 'A'
            obj.verified = True
            obj.save()
        if(actionType == 'reject') :
            obj.status = 'R'
            obj.verified =  True
            obj.save()
        return redirect('index')
        # return render(request , 'index.html') 
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

def details(request, crime_id):
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

    return render(request, 'details.html', context)

@csrf_exempt
def fetch_number_plate_data(request, crime_id):
    crime_event = get_object_or_404(CapturedImage, id=crime_id)

    # Assuming you have the image loaded into the 'image' variable using OpenCV
    image = cv2.imread(crime_event.image.path)

    # Encode the image as JPEG
    success, image_jpg = cv2.imencode('.jpg', image)
    if not success:
        return JsonResponse({'error': 'Error encoding image'})

    # Convert the image data to bytes
    image_bytes = image_jpg.tobytes()

    # Set the Plate Recognizer API endpoint and token
    api_url = 'https://api.platerecognizer.com/v1/plate-reader/'
    api_token = '1b176e989995c152ad27759e1fbc097ca4ac77f1'  # Replace with your actual API token

    # Set the headers with the Authorization token
    headers = {'Authorization': f'Token {api_token}'}

    # Create a dictionary with the file data
    files = {'upload': ('image.jpg', image_bytes, 'image/jpeg')}

    # Send the POST request to the Plate Recognizer API
    response = requests.post(api_url, headers=headers, files=files)

    # Check the response
    if response.status_code == 201 or response.status_code == 200:
        # Successful response
        results = response.json()["results"]

        # return JsonResponse({'results': results})

        # Extract information from the results
        if results:
            # Sort candidates based on score in descending order
            candidates = sorted(results[0]["candidates"], key=lambda x: x["score"], reverse=True)

            # Extract the number on the plate with the highest score
            highest_score_plate = candidates[0]["plate"]

            # Extract the vehicle type
            vehicle_type = results[0]["vehicle"]["type"]

            return JsonResponse({'plate': highest_score_plate, 'vehicle_type': vehicle_type})
        else:
            return JsonResponse({'error': 'No results found'})
    else:
        # Error handling
        return JsonResponse({'error': f'Error: {response.status_code}', 'response_content': response.text})

# def store(request):
#     if request.method == "POST": 
#         print('post request')
#         avail  = request.POST.get('avail')
#         user_reports = CapturedImage.objects.filter(reported_by=request.user)
#         approved = user_reports.filter(status='A')

#         total_rewards = approved.aggregate(Sum('rewards'))['rewards__sum']
#         total_rewards = total_rewards -  avail
#         print(total_rewards)
#         total_rewards = total_rewards if total_rewards is not None else 0
#         context = {
#             'total_rewards': total_rewards,
#         }

#     elif request.user.is_authenticated:
#         user_reports = CapturedImage.objects.filter(reported_by=request.user)
#         approved = user_reports.filter(status='A')

#         total_rewards = approved.aggregate(Sum('rewards'))['rewards__sum']
#         total_rewards = total_rewards if total_rewards is not None else 0

#         context = {
#             'total_rewards': total_rewards,
#         }
#     else:
#         redirect('login')
#     return render(request, 'store.html',{'total_rewards':total_rewards})

def store(request):
    if request.method == "POST":
        print('post request')
        avail_str = request.POST.get('avail', '0')  # Default to '0' if not provided
        try:
            avail = float(avail_str)
        except ValueError:
            # Handle the case where 'avail' is not a valid float
            avail = 0

        user_reports = CapturedImage.objects.filter(reported_by=request.user)
        approved = user_reports.filter(status='A')

        total_rewards = approved.aggregate(Sum('rewards'))['rewards__sum'] or 0
        total_rewards -= avail
        print(total_rewards)
        total_rewards = max(total_rewards, 0)  # Ensure total_rewards is not negative

        context = {
            'total_rewards': total_rewards,
        }

    elif request.user.is_authenticated:
        user_reports = CapturedImage.objects.filter(reported_by=request.user)
        approved = user_reports.filter(status='A')

        total_rewards = approved.aggregate(Sum('rewards'))['rewards__sum'] or 0

        context = {
            'total_rewards': total_rewards,
        }
    else:
        return redirect('login')

    return render(request, 'store.html', context)
  
