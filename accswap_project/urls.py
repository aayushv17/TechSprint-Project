from django.contrib import admin
from django.urls import path, include

# This is the root URL configuration for the entire project.
# It's the first place Django looks when a request comes in.
urlpatterns = [
    # The URL for Django's built-in admin site.
    path('admin/', admin.site.urls),

    # This is the most important line for our application.
    # It tells Django: "For any URL that starts with 'api/',
    # hand off the rest of the URL processing to the file located at 'api.urls'".
    # This keeps our project organized by delegating app-specific URLs to the app itself.
    path('api/', include('api.urls')),
]

# accswap_project/urls.py
from django.contrib import admin
from django.urls import path, include
# --- Add these two imports ---
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]

# --- Add this line at the end ---
# This tells Django to serve files from your STATIC_URL path during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)