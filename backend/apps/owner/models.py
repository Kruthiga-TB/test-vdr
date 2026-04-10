from django.db import models

# Create your models here.
class Plan(models.Model):
    PLAN_CHOICES = [
        ("starter", "Starter"),
        ("pro", "Pro"),
        ("premium", "Premium"),
    ]

    name = models.CharField(max_length=20, choices=PLAN_CHOICES, unique=True)

    # price = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    max_users = models.IntegerField(null=True, blank=True)
    storage_gb = models.IntegerField(null=True, blank=True)
    projects = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):

        if self.name == "starter":
            self.price = 499
            self.max_users = 5
            self.storage_gb = 1
            self.projects = 1

        elif self.name == "pro":
            self.price = 1499
            self.max_users = 10
            self.storage_gb = 10
            self.projects = 1

        elif self.name == "premium":
            self.price = 4999
            self.max_users = 999999  # unlimited
            self.storage_gb = 100
            self.projects = 5

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name   # 👈 typo fix panniten (nam → name)
