from django.apps import AppConfig
import logging

class DomainIsolationConfig(AppConfig):
    name = 'domainIsolationPlugin'
    verbose_name = "Domain Isolation Native Unlocker"

    def ready(self):
        # This code runs when CyberPanel loads the plugin!
        try:
            from packages.packagesManager import PackagesManager
            
            # Save the original method just in case
            if not hasattr(PackagesManager, 'original_checkAddonAccess'):
                PackagesManager.original_checkAddonAccess = PackagesManager.checkAddonAccess
                
            # Override the method to always return True natively
            @staticmethod
            def bypass_addon_access():
                return True
                
            PackagesManager.checkAddonAccess = bypass_addon_access
            logging.info("[Domain Isolation Plugin] Successfully bypassed CyberPanel Addon check for Resource Limits!")
        except Exception as e:
            logging.error(f"[Domain Isolation Plugin] Failed to apply native patch: {str(e)}")
