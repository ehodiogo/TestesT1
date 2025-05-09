"""
URL configuration for Projeto project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from Projeto.settings import DEBUG, MEDIA_ROOT, MEDIA_URL
from pcap.views import upload_pcap, dividir_pcap_view, verificar_status_task

urlpatterns = [
    path('admin/', admin.site.urls),
    path('process', upload_pcap),
    path('split', dividir_pcap_view),
    path('verificar-status/<str:task_id>/', verificar_status_task, name='verificar_status_task'),

]

if DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)

