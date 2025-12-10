# webbank/accounts/management/commands/seed_users.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal # Import Decimal for monetary values
from accounts.models import User as CustomUser # Import your custom User model
from shares.models import Share # Import the Share model

class Command(BaseCommand):
    help = 'Seeds the database with various types of users (admin, member, director, etc.)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Seeding users...'))

        User = get_user_model()

        # Clear existing custom users and their related Share objects
        # Be cautious with this in production environments!
        self.stdout.write(self.style.WARNING('Clearing existing custom users and their associated shares...'))
        CustomUser.objects.filter(is_superuser=False).delete() # Keep Django's default admin if it exists
        # Share objects are CASCADE deleted with User, but explicitly clear for safety/idempotence
        # Share.objects.all().delete() # This might be too aggressive if some users remain

        user_data = [
            {'username': 'adminuser', 'email': 'admin@example.com', 'user_type': 'admin', 'is_staff': True, 'is_superuser': True},
            {'username': 'founderuser', 'email': 'founder@example.com', 'user_type': 'founder', 'is_staff': True, 'is_superuser': False},
            {'username': 'director1', 'email': 'director1@example.com', 'user_type': 'director'},
            {'username': 'director2', 'email': 'director2@example.com', 'user_type': 'director'},
            {'username': 'member1', 'email': 'member1@example.com', 'user_type': 'member'},
            {'username': 'member2', 'email': 'member2@example.com', 'user_type': 'member'},
            {'username': 'member3', 'email': 'member3@example.com', 'user_type': 'member', 'monthly_share_target': Decimal('5000.00')}, # Example with target
            {'username': 'guarantor1', 'email': 'guarantor1@example.com', 'user_type': 'guarantor'},
        ]

        for data in user_data:
            username = data['username']
            email = data['email']
            user_type = data['user_type']
            is_staff = data.get('is_staff', False)
            is_superuser = data.get('is_superuser', False)
            monthly_share_target = data.get('monthly_share_target', Decimal('0.00')) # Default to 0.00

            try:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='password123', # Default password for all seeded users
                    user_type=user_type,
                    is_staff=is_staff,
                    is_superuser=is_superuser,
                )
                self.stdout.write(self.style.SUCCESS(f'Created user: {username} ({user_type})'))

                # Create a Share object for members/guarantors and users with targets
                if user_type in ['member', 'guarantor'] or monthly_share_target > 0:
                    share, created = Share.objects.get_or_create(
                        member=user,
                        defaults={'monthly_share_target': monthly_share_target}
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Created Share object for {username} with target {monthly_share_target}'))
                    else:
                        share.monthly_share_target = monthly_share_target
                        share.save()
                        self.stdout.write(self.style.SUCCESS(f'Updated Share object for {username} with target {monthly_share_target}'))


            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating user {username}: {e}'))

        self.stdout.write(self.style.SUCCESS('User seeding complete.'))
