# managerpanel/templatetags/manager_tags.py
from django import template
# Use relative import if models.py is in the same app
from ..models import ManagerProfile

register = template.Library()

@register.simple_tag
def is_manager_user(user):
    """Checks if a user has an active ManagerProfile."""
    if not user.is_authenticated:
        return False
    try:
        return user.managerprofile.is_manager
    except ManagerProfile.DoesNotExist:
        return False
    except AttributeError: # Handles cases like AnonymousUser more explicitly
         return False