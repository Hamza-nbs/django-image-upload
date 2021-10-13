from django.conf.urls import url
from .views import FileView, test_view


urlpatterns = [
    url(r'^upload/$', FileView.as_view(), name='file-upload'),
    url(r'^test/$', test_view),
]
