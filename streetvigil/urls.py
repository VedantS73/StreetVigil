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
    path('upload', upload, name='upload'),
    path('report_interface', report_interface, name='report_interface'),  # Unique name
    path('submit_report/', report_submission_view, name='submit_report'),
    path('success_page', success_page, name='success_page'),

    # Police View
    path('police', police, name='police'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
