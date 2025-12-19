from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from members_amor108.models import Member, MembershipStatus # Import MembershipStatus
from amor108.models import Pool
from accounts_amor108.models import Amor108Profile, Role # Import Amor108Profile and Role
from django.db import IntegrityError

class Command(BaseCommand):
    help = 'Seeds the database with a test Amor108 member.'

    def handle(self, *args, **options):
        User = get_user_model()

        # Create a test user
        username = 'testuser_amor108@example.com'
        email = 'testuser_amor108@example.com'
        password = 'testpassword' # A known password for testing

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name='Amor108',
                last_name='TestMember',
                user_type='member',
                is_active=True # Set to active for immediate login
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully created test user: {user.username}'))
        except IntegrityError:
            user = User.objects.get(username=username)
            self.stdout.write(self.style.WARNING(f'Test user {user.username} already exists.'))

        # Get or create the default 'Member' role
        member_role, created_role = Role.objects.get_or_create(name='Member', defaults={'description': 'Regular Amor108 member'})
        if created_role:
            self.stdout.write(self.style.SUCCESS(f'Created Role: {member_role.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Using existing Role: {member_role.name}'))

        # Create or update Amor108Profile for the user and set to approved
        try:
            profile, created_profile = Amor108Profile.objects.get_or_create(
                user=user,
                defaults={'role': member_role, 'is_approved': True}
            )
            if not created_profile:
                # If profile already exists, ensure it's approved and has the correct role
                if not profile.is_approved or profile.role != member_role:
                    profile.is_approved = True
                    profile.role = member_role
                    profile.save()
                    self.stdout.write(self.style.SUCCESS(f'Updated existing Amor108Profile for {user.username} to be approved with role {member_role.name}.'))
                else:
                    self.stdout.write(self.style.WARNING(f'Amor108Profile for {user.username} already exists and is approved with role {member_role.name}.'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Successfully created approved Amor108Profile for user: {user.username} with role {member_role.name}.'))
        except IntegrityError:
            self.stdout.write(self.style.ERROR(f'Failed to create/update Amor108Profile for {user.username}.'))

        # Get the first available pool, or create one if none exist
        pool, created = Pool.objects.get_or_create(
            name='GOLD', # Use 'GOLD' as a known pool name from create_pools
            defaults={'contribution_amount': 10000, 'contribution_frequency': 'monthly'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created default pool: {pool.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Using existing pool: {pool.name}'))

        # Get or create the 'approved' MembershipStatus instance
        approved_status, created_status = MembershipStatus.objects.get_or_create(name='Approved', defaults={'description': 'Member application has been approved.'})
        if created_status:
            self.stdout.write(self.style.SUCCESS(f'Created MembershipStatus: {approved_status.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Using existing MembershipStatus: {approved_status.name}'))

        # Create a test Amor108 member
        try:
            member, created = Member.objects.get_or_create(
                user=user,
                defaults={'pool': pool, 'status': approved_status} # Pass the MembershipStatus instance
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully created Amor108 member for user: {user.username}'))
            else:
                self.stdout.write(self.style.WARNING(f'Amor108 member for user {user.username} already exists.'))
        except IntegrityError:
            self.stdout.write(self.style.ERROR(f'Failed to create Amor108 member for {user.username}. It might already exist or there is a data issue.'))

        self.stdout.write(self.style.SUCCESS('Amor108 test member seeding complete.'))