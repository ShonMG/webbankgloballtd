
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webbank.settings')
django.setup()

from members_amor108.models import Member
from pools.models import Pool

def update_member_pool_fk():
    print("--- Updating Member's Pool Foreign Key ---")

    try:
        # 1. Get the problematic Member object (as per your error message)
        member_pk_to_update = 2 # This was the PK from your IntegrityError
        member_to_update = Member.objects.get(pk=member_pk_to_update)
        print(f"Found Member with pk={member_pk_to_update}: {member_to_update.user.username}")

        # 2. Get an existing Pool object to link to
        #    You can change this to a specific pool if you know its ID or name
        existing_pool = Pool.objects.first() 
        if not existing_pool:
            print("No existing Pool objects found in the database. Please create one first.")
            return

        print(f"Linking to existing Pool: {existing_pool.name} (ID: {existing_pool.id})")

        # 3. Update the Member's pool foreign key
        member_to_update.pool = existing_pool
        member_to_update.save()
        
        print(f"Successfully updated Member {member_to_update.user.username} (pk={member_pk_to_update}) to point to Pool '{existing_pool.name}'.")

    except Member.DoesNotExist:
        print(f"Member with pk={member_pk_to_update} does not exist. No update performed.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    update_member_pool_fk()
