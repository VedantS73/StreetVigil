from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import *

urlpatterns = [
    # Authentication Routes
    path("login", login_view, name="login"),
    path("logout", logout_view, name="logout"),
    path("register", register, name="register"),

    # Pages
    path('', index, name='index'),
    path('capture', capture, name='capture'),
    path('aftercapture', aftercapture, name='aftercapture'),
    path('upload', upload, name='upload'),
    path('report_interface', report_interface, name='report_interface'),  # Unique name
    path('submit_report/', report_submission_view, name='submit_report'),
    path('success_page', success_page, name='success_page'),
    path('details/<int:crime_id>/', details, name='details'),

    # Police View
    path('police', police, name='police'),
    path('crime_report/<int:crime_id>/', crime_report, name='crime_report'),
    path('fetch_number_plate_data/<int:crime_id>/', fetch_number_plate_data, name='fetch_number_plate_data'),

    # Clain Stores
    path('store', store, name='store'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
