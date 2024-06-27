from django.db import models
from django.utils import timezone

class UserDescription(models.Model):

    botid = models.CharField(max_length=255)
    description = models.TextField()
    interaction_style = models.CharField(max_length=50,null=True)
    url_data = models.JSONField(null=True) # Assuming you want an empty list as default
    created_at = models.DateTimeField(auto_now_add=True)
    history_list = models.JSONField(null=True, blank=True)
    train_status = models.BooleanField(default=False)
    


    def check_interaction_style_and_description(self):
        if self.interaction_style is not None and self.description is not None:
            # Add your additional code here
            # For example:
            # process_interaction_style(self.interaction_style)
            # process_description(self.description)
            return True
        else:
            return False