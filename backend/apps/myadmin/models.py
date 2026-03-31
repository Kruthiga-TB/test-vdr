from django.db import models

# Create your models here.


from django.db import models

class Plan(models.Model):
    name = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class PlanFeature(models.Model):
    plan = models.OneToOneField(Plan, on_delete=models.CASCADE, related_name="features")

    max_users = models.IntegerField(null=True, blank=True)
    storage_gb = models.IntegerField(null=True, blank=True)
    projects = models.IntegerField(null=True, blank=True)
    full_data_room = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.plan.name} Features"