from django.db import models

class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    tech_stack = models.CharField(max_length=200) # e.g., "Python, PyTorch"
    github_link = models.URLField(blank=True)
    image = models.ImageField(upload_to='projects/', blank=True)

    def __cl__(self):
        return self.title