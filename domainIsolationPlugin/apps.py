from django.apps import AppConfig
from django.core.signals import request_started
import logging

class DomainIsolationConfig(AppConfig):
    name = 'domainIsolationPlugin'
    verbose_name = "Domain Isolation Native Unlocker"
    patched = False

    def apply_patch(self, sender, **kwargs):
        if self.patched:
            return
            
        try:
            from packages.packagesManager import PackagesManager
            
            if not hasattr(PackagesManager, 'original_checkAddonAccess'):
                PackagesManager.original_checkAddonAccess = PackagesManager.checkAddonAccess
                
            @staticmethod
            def bypass_addon_access():
                return True
                
            PackagesManager.checkAddonAccess = bypass_addon_access
            self.patched = True
            logging.info("[Domain Isolation Plugin] Successfully bypassed CyberPanel Addon check for Resource Limits!")
        except Exception as e:
            logging.error(f"[Domain Isolation Plugin] Failed to apply native patch: {str(e)}")

    def ready(self):
        # Apply the patch safely on the first HTTP request to avoid populate() errors
        request_started.connect(self.apply_patch)
