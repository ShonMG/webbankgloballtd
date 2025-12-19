# webbank/accounts/management/commands/seed_users.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal # Import Decimal for monetary values
from accounts.models import User as CustomUser # Import your custom User model
from shares.models import Share # Import the Share model
from members_amor108.models import Member as Amor108Member, MembershipStatus # Import Member and MembershipStatus
from amor108.models import Pool # Import Pool
from django.db import IntegrityError # Import IntegrityError

class Command(BaseCommand):
    help = 'Seeds the database with various types of users (admin, member, director, etc.)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Seeding users...'))

        User = get_user_model()

        # Clear existing custom users and their associated shares
        self.stdout.write(self.style.WARNING('Clearing existing custom users and their associated shares...'))
        CustomUser.objects.filter(is_superuser=False).delete()
        # Share objects are CASCADE deleted with User, but explicitly clear related members_amor108.Member as well
        Amor108Member.objects.all().delete()
        
        # Get or create a default MembershipStatus (e.g., 'Approved') and a default Pool
        approved_status, _ = MembershipStatus.objects.get_or_create(
            name='Approved',
            defaults={'description': 'Member application has been approved.'}
        )
        default_pool, _ = Pool.objects.get_or_create(
            name='GOLD', # Assuming 'GOLD' is created by create_pools command
            defaults={'contribution_amount': 10000, 'contribution_frequency': 'monthly'}
        )


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
                # Create or get the User
                user, user_created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'password': 'password123', # Set default password only on creation
                        'user_type': user_type,
                        'is_staff': is_staff,
                        'is_superuser': is_superuser,
                    }
                )
                if user_created:
                    user.set_password('password123') # Set password securely
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f'Created user: {username} ({user_type})'))
                else:
                    self.stdout.write(self.style.WARNING(f'User {username} already exists.'))
                    # Ensure user details are consistent if user existed
                    user.email = email
                    user.user_type = user_type
                    user.is_staff = is_staff
                    user.is_superuser = is_superuser
                    user.save()


                # Create Amor108Member instance if user_type is 'member' or 'guarantor'
                amor108_member_instance = None
                if user_type in ['member', 'guarantor']:
                    try:
                        amor108_member_instance, created = Amor108Member.objects.get_or_create(
                            user=user,
                            defaults={'status': approved_status, 'pool': default_pool}
                        )
                        if created:
                            self.stdout.write(self.style.SUCCESS(f'Created Amor108Member for {username}'))
                        else:
                            self.stdout.write(self.style.WARNING(f'Amor108Member for {username} already exists.'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error creating Amor108Member for {username}: {e}'))

                # Create a Share object, linked to Amor108Member
                if amor108_member_instance:
                    share, created = Share.objects.get_or_create(
                        member=amor108_member_instance, # Use the Amor108Member instance
                        defaults={'monthly_share_target': monthly_share_target}
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Created Share object for {username} with target {monthly_share_target}'))
                    else:
                        share.monthly_share_target = monthly_share_target
                        share.save()
                        self.stdout.write(self.style.SUCCESS(f'Updated Share object for {username} with target {monthly_share_target}'))
                elif user_type in ['member', 'guarantor'] or monthly_share_target > 0:
                     self.stdout.write(self.style.WARNING(f'Skipping Share creation for {username} as no Amor108Member instance was created.'))

            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f'IntegrityError creating user {username}: {e}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Unexpected error creating user {username}: {e}'))

        self.stdout.write(self.style.SUCCESS('User seeding complete.'))
