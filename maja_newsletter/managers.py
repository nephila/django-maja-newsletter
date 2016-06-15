"""Managers for maja_newsletter"""
from django.db import models


class ContactManager(models.Manager):
    """Manager for the contacts"""

    def subscribers(self):
        """Return all subscribers"""
        return self.get_queryset().filter(subscriber=True)

    def unsubscribers(self):
        """Return all unsubscribers"""
        return self.get_queryset().filter(subscriber=False)

    def valids(self):
        """Return only valid contacts"""
        return self.get_queryset().filter(valid=True)

    def valid_subscribers(self):
        """Return only valid subscribers"""
        return self.subscribers().filter(valid=True)
