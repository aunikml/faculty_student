# managerpanel/apps.py
from django.apps import AppConfig
import importlib # Import the module explicitly for clarity if needed

class ManagerPanelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'managerpanel'
    verbose_name = "Manager Panel" # Optional: Nicer name in admin

    def ready(self):
        # This method is called when Django starts and the app registry is fully populated.
        # It's the recommended place to import signals.
        try:
            # Import the module containing your signal receivers.
            # If your signals are in models.py:
            importlib.import_module(f'{self.name}.models')
            # Or if you created a separate signals.py:
            # importlib.import_module(f'{self.name}.signals')
            print(f"{self.verbose_name}: Signals imported successfully.") # Debug print
        except ImportError as e:
            # Indent the contents of the except block correctly
            print(f"Warning: Could not import models/signals for {self.name} during app ready: {e}")
            # You might want to log this error instead of just printing
            pass # This pass belongs to the except block

# Note: Ensure managerpanel/__init__.py contains:
# default_app_config = 'managerpanel.apps.ManagerPanelConfig'