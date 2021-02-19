from django.db import models

# Create your models here.

class Product(models.Model):
    name = models.CharField(max_length=50)
    price = models.IntegerField()

    def __str__(self):
        return self.name

    def stripe_price(self):
        return self.price * 100

    def get_url(self):
        return 'http://google.com'
    
