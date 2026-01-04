
import os
import django
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webbank.settings')
django.setup()

from django.contrib.auth import get_user_model
from pools.models import Pool, Resolution
from accounts_amor108.models import Amor108Profile

User = get_user_model()

def create_initial_data():
    print("--- Seeding Initial Pool Data ---")

    # 1. Create or get a default manager user
    try:
        manager_user = User.objects.get(email='admin@webbank.com')
        print("Found existing manager user: admin@webbank.com")
    except User.DoesNotExist:
        manager_user = User.objects.create_superuser(
            username='webbankadmin',
            email='admin@webbank.com',
            password='adminpassword',
            first_name='Webbank',
            last_name='Admin',
            user_type='admin'
        )
        print("Created new manager user: webbankadmin (admin@webbank.com)")

    # 2. Create various Pool objects
    pools_to_create = [
        {
            'name': 'Bronze Tier',
            'description': 'Entry-level pool with basic benefits.',
            'contribution_amount': Decimal('500.00'),
            'contribution_frequency': 'MONTHLY',
            'member_limit': 100,
            'is_active': True,
        },
        {
            'name': 'Silver Tier',
            'description': 'Intermediate pool with enhanced benefits.',
            'contribution_amount': Decimal('1500.00'),
            'contribution_frequency': 'MONTHLY',
            'member_limit': 50,
            'is_active': True,
        },
        {
            'name': 'Gold Tier',
            'description': 'Premium pool with full benefits and voting privileges.',
            'contribution_amount': Decimal('5000.00'),
            'contribution_frequency': 'MONTHLY',
            'member_limit': 20,
            'is_active': True,
        },
        {
            'name': 'Diamond Tier',
            'description': 'Exclusive tier for top contributors.',
            'contribution_amount': Decimal('10000.00'),
            'contribution_frequency': 'MONTHLY',
            'member_limit': 10,
            'is_active': True,
            'is_locked': True, # Example of a locked pool
        },
    ]

    created_pools = {}
    for pool_data in pools_to_create:
        pool_data['manager'] = manager_user
        pool, created = Pool.objects.get_or_create(name=pool_data['name'], defaults=pool_data)
        if created:
            print(f"Created Pool: {pool.name}")
        else:
            print(f"Pool already exists: {pool.name}")
        created_pools[pool.name] = pool
    
    # 3. Create or get a default test user
    try:
        test_user = User.objects.get(email='test@webbank.com')
        print("Found existing test user: test@webbank.com")
    except User.DoesNotExist:
        test_user = User.objects.create_user(
            username='testuser',
            email='test@webbank.com',
            password='testpassword',
            first_name='Test',
            last_name='User',
            user_type='member'
        )
        print("Created new test user: testuser (test@webbank.com)")

    # 4. Create or get Amor108Profile for the test user and assign to a pool
    test_profile, created = Amor108Profile.objects.get_or_create(user=test_user)
    if created:
        print(f"Created Amor108Profile for {test_user.username}")
    else:
        print(f"Found existing Amor108Profile for {test_user.username}")
    
    if test_profile.membership_pool is None and 'Bronze Tier' in created_pools:
        test_profile.membership_pool = created_pools['Bronze Tier']
        test_profile.save()
        created_pools['Bronze Tier'].members.add(test_user)
        print(f"Assigned {created_pools['Bronze Tier'].name} to {test_user.username} and added to pool members.")
    elif test_profile.membership_pool:
        print(f"{test_user.username} is already in pool: {test_profile.membership_pool.name}")
    else:
        print("Could not assign test user to a pool (Bronze Tier not found or user already in a pool).")

    # 5. Create some Resolution objects
    resolutions_to_create = [
        {
            'title': 'Approve Q4 Budget',
            'description': 'Proposal to approve the budget for the fourth quarter of the fiscal year.',
            'visible_to_all': True,
            'votable_by_gold_only': False,
            'created_by': manager_user,
            'pool': None, # Global resolution
        },
        {
            'title': 'New Investment Opportunity',
            'description': 'Proposal to invest in a new agricultural project. Requires Gold Tier approval.',
            'visible_to_all': True,
            'votable_by_gold_only': True,
            'created_by': manager_user,
            'pool': created_pools.get('Gold Tier', None), # Specific to Gold Tier or general
        },
        {
            'title': 'Amend Contribution Frequency',
            'description': 'Discuss and vote on changing contribution frequency options.',
            'visible_to_all': False, # Not visible to all
            'votable_by_gold_only': False,
            'created_by': manager_user,
            'pool': created_pools.get('Silver Tier', None), # Specific to Silver Tier
        }
    ]

    for res_data in resolutions_to_create:
        resolution_pool = res_data.pop('pool') # Extract pool separately
        resolution, created = Resolution.objects.get_or_create(
            title=res_data['title'],
            defaults={**res_data, 'pool': resolution_pool}
        )
        if created:
            print(f"Created Resolution: {resolution.title}")
        else:
            print(f"Resolution already exists: {resolution.title}")
    
    print("--- Seeding Complete ---")

if __name__ == '__main__':
    create_initial_data()
