from django.db import models
from accounts.models import User

class Document(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='documents', help_text="The owner of the document. If empty, it's a general document.")

    def __str__(self):
        return self.title