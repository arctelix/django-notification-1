from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext_noop as _
from notification import models as notification
from django.conf import settings
from .. import create_notice_types

class Command(BaseCommand):

    help = 'updates the database with the latest notice type definitions'
  
    def handle(self, *args, **options):
        create_notice_types()
        
        
        
        
        
        
