from django.conf.urls import url
from infoextr import views

urlpatterns = [
    url(r'^$',views.email_submission,name='email_submission'),
    #url(r'^$',views.detail,name='detail'),

]
