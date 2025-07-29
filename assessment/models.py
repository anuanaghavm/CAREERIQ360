from django.db import models

class Theory(models.Model):
    content = models.CharField(max_length=100)

    def __str__(self):
        return self.content

class Test(models.Model):
    name = models.TextField()

    def __str__(self):
        return self.name

class Assessment(models.Model):
    age_group = models.CharField(max_length=255)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    theory = models.ForeignKey(Theory, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.age_group

