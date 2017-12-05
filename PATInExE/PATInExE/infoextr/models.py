from django.db import models

# Create your models here.
class User(models.Model):
    Ticketid= models.CharField(max_length = 265,primary_key=True)
    Dateofjourney = models.CharField(max_length =265 )
    Sheduletime = models.CharField(max_length =265 )
    Source = models.CharField(max_length =265 )
    Destination = models.CharField(max_length =265 )
    Phonenumber = models.CharField(max_length =265 )
    Status = models.CharField(max_length =265 )
