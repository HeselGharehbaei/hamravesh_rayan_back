import json
import threading
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from core.middleware import get_current_user  # Import function from middleware

# _old_values = {}  # Store old values temporarily
# _log_triggered = set()  # Keep track of logged instances to avoid duplicates

# @receiver(pre_save)
# def store_old_values(sender, instance, **kwargs):
#     """Store old values before saving the instance."""
#     if not instance.pk:  # Skip new objects
#         return

#     try:
#         old_instance = sender.objects.get(pk=instance.pk)
#     except sender.DoesNotExist:
#         return  # Skip if object doesn't exist

#     _old_values[instance.pk] = {
#         field.name: getattr(old_instance, field.name, "نامشخص")
#         for field in instance._meta.fields
#     }

# @receiver(post_save)
# def log_changes(sender, instance, created, **kwargs):
#     """Log changes after saving the instance."""
#     if created:  # Skip logging for newly created objects
#         return

#     if instance.pk in _log_triggered:  # Skip if already logged
#         return

#     old_data = _old_values.pop(instance.pk, {})  # Retrieve old values
#     changes = {}

#     for field in instance._meta.fields:
#         field_name = field.name
#         old_value = old_data.get(field_name, "نامشخص")
#         new_value = getattr(instance, field_name, "نامشخص")

#         if old_value != new_value:  # Only log if the field value has actually changed
#             changes[field_name] = {"old": old_value, "new": new_value}

#     if changes:  # Log only if there are actual changes
#         user = get_current_user()  # Get the user from thread-local storage
#         LogEntry.objects.log_action(
#             user_id=user.pk if user and user.is_authenticated else None,  # Ensure user is authenticated
#             content_type_id=ContentType.objects.get_for_model(instance).pk,
#             object_id=instance.pk,
#             object_repr=str(instance),
#             action_flag=CHANGE,
#             change_message=json.dumps(changes, default=str),  # Save old & new values in JSON format
#         )

#         # Mark this instance as logged to prevent duplicate log entries
#         _log_triggered.add(instance.pk)

###new
# import json
# import threading
# from django.db.models.signals import pre_save, post_save
# from django.dispatch import receiver
# from django.contrib.admin.models import LogEntry, CHANGE
# from django.contrib.contenttypes.models import ContentType

# _old_values = {}  # Store old values temporarily
# _log_triggered = threading.local()  # Thread-local storage for preventing double logging

# # def get_current_user():
# #     """Retrieve the user from thread-local storage."""
# #     return getattr(threading.local(), "user", None)

# @receiver(pre_save)
# def store_old_values(sender, instance, **kwargs):
#     """Store old values before saving the instance."""
#     if not instance.pk:  # Skip new objects
#         return

#     try:
#         old_instance = sender.objects.get(pk=instance.pk)
#     except sender.DoesNotExist:
#         return  # Skip if object doesn't exist

#     _old_values[instance.pk] = {
#         field.name: getattr(old_instance, field.name, "نامشخص")
#         for field in instance._meta.fields
#     }

# @receiver(post_save)
# def log_changes(sender, instance, created, **kwargs):
#     """Log changes after saving the instance."""
#     if created:  # Skip logging for newly created objects
#         return

#     # Avoid double logging by using thread-local storage
#     if getattr(_log_triggered, 'already_logged', False):
#         return

#     old_data = _old_values.pop(instance.pk, {})  # Retrieve old values
#     changes = {}

#     for field in instance._meta.fields:
#         field_name = field.name
#         old_value = old_data.get(field_name, "نامشخص")
#         new_value = getattr(instance, field_name, "نامشخص")

#         if old_value != new_value:  # Only log if the field value has actually changed
#             changes[field_name] = {"old": old_value, "new": new_value}

#     if changes:  # Log only if there are actual changes
#         user = get_current_user()  # Get the user from thread-local storage
        
#         if not user:  # If no user, set it to None
#             user = None
        
#         LogEntry.objects.log_action(
#             user_id=user.pk if user and user.is_authenticated else None,  # Ensure user is either valid or None
#             content_type_id=ContentType.objects.get_for_model(instance).pk,
#             object_id=instance.pk,
#             object_repr=str(instance),
#             action_flag=CHANGE,
#             change_message=json.dumps(changes, default=str),  # Save old & new values in JSON format
#         )
        
#         # Mark this instance as logged to prevent duplicate log entries
#         _log_triggered.already_logged = True
#         print(_log_triggered.already_logged)

#     # Reset the flag after the signal is done
#     _log_triggered.already_logged = False

