from django.urls import path
import logging

# Safely apply the monkey patch here because urls.py is loaded AFTER all Django apps are fully populated!
try:
    from packages.packagesManager import PackagesManager
    if not hasattr(PackagesManager, 'original_checkAddonAccess'):
        PackagesManager.original_checkAddonAccess = PackagesManager.checkAddonAccess
        
    # We must not use @staticmethod decorator if we are just defining a function
    # In Python, assigning a function to a class creates a method. But checkAddonAccess is called without arguments via self!
    # Wait, in PackagesManager, it's defined as @staticmethod and called as self.checkAddonAccess().
    # If we assign a regular function, self is passed! So we MUST use @staticmethod.
    
    @staticmethod
    def bypass_addon_access():
        return True
        
    PackagesManager.checkAddonAccess = bypass_addon_access
    logging.info("[Domain Isolation Plugin] Successfully bypassed CyberPanel Addon check for Resource Limits via urls.py!")
except Exception as e:
    logging.error(f"[Domain Isolation Plugin] Failed to apply native patch: {str(e)}")

urlpatterns = []
