from django.apps import AppConfig
import logging
import threading

class DomainIsolationConfig(AppConfig):
    name = 'domainIsolationPlugin'
    verbose_name = "Domain Isolation Native Unlocker"

    def apply_patch(self):
        try:
            from packages.packagesManager import PackagesManager
            
            if not hasattr(PackagesManager, 'original_checkAddonAccess'):
                PackagesManager.original_checkAddonAccess = PackagesManager.checkAddonAccess
                
            @staticmethod
            def bypass_addon_access():
                return True
                
            PackagesManager.checkAddonAccess = bypass_addon_access
            logging.info("[Domain Isolation Plugin] Successfully bypassed CyberPanel Addon check for Resource Limits!")
        except Exception as e:
            logging.error(f"[Domain Isolation Plugin] Failed to apply native patch: {str(e)}")

    def ready(self):
        # Defer the import by 2 seconds to avoid Django's "populate() isn't reentrant" error
        threading.Timer(2.0, self.apply_patch).start()
