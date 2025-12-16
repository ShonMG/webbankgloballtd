from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from amor108.models import Pool, Member
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

        # Get the first available pool, or create one if none exist
        pool, created = Pool.objects.get_or_create(
            name='12 members contributing Ksh 10,000 per month', # Use an existing pool name
            defaults={'contribution_amount': 10000, 'contribution_frequency': 'monthly'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created default pool: {pool.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Using existing pool: {pool.name}'))

        # Create a test Amor108 member
        try:
            member, created = Member.objects.get_or_create(
                user=user,
                defaults={'pool': pool, 'status': 'approved'}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully created Amor108 member for user: {user.username}'))
            else:
                self.stdout.write(self.style.WARNING(f'Amor108 member for user {user.username} already exists.'))
        except IntegrityError:
            self.stdout.write(self.style.ERROR(f'Failed to create Amor108 member for {user.username}. It might already exist or there is a data issue.'))

        self.stdout.write(self.style.SUCCESS('Amor108 test member seeding complete.'))
