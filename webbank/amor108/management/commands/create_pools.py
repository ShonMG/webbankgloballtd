from django.core.management.base import BaseCommand
from amor108.models import Pool

class Command(BaseCommand):
    help = 'Creates initial Pool objects for membership types.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Creating Pool objects...")

        # Clear existing pools to prevent duplicates if run multiple times
        Pool.objects.all().delete()
        self.stdout.write("Deleted existing Pool objects (if any).")

        # GOLD
        Pool.objects.create(name='GOLD', contribution_amount=10000, contribution_frequency='monthly')

        # FIRST CLASS
        Pool.objects.create(name='FIRST CLASS', contribution_amount=7500, contribution_frequency='monthly')
        Pool.objects.create(name='FIRST CLASS', contribution_amount=5000, contribution_frequency='monthly')

        # MIDDLE CLASS
        Pool.objects.create(name='MIDDLE CLASS', contribution_amount=100, contribution_frequency='daily')
        Pool.objects.create(name='MIDDLE CLASS', contribution_amount=2500, contribution_frequency='monthly')

        # ECONOMIC CLASS
        Pool.objects.create(name='ECONOMIC CLASS', contribution_amount=50, contribution_frequency='daily')
        Pool.objects.create(name='ECONOMIC CLASS', contribution_amount=1000, contribution_frequency='monthly')
        Pool.objects.create(name='ECONOMIC CLASS', contribution_amount=500, contribution_frequency='monthly')

        self.stdout.write(self.style.SUCCESS("Successfully created Pool objects:"))
        for p in Pool.objects.all():
            self.stdout.write(f'- {p.name}: Ksh {p.contribution_amount} ({p.contribution_frequency})')
