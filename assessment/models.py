from django.db import models

class AgeGroup(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Theory(models.Model):
    content = models.TextField()

    def __str__(self):
        return self.title

class Assessment(models.Model):
    test_name = models.CharField(max_length=255)
    age_group = models.ForeignKey(AgeGroup, on_delete=models.CASCADE)
    theory = models.ForeignKey(Theory, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.test_name

