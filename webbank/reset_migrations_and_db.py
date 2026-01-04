
import os
import shutil
import subprocess
import sys

# Define your Django project root (where manage.py is located)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Define the path to your database file
DB_FILE = os.path.join(PROJECT_ROOT, 'db.sqlite3')

# Define the apps whose migrations should be deleted and recreated
# Make sure to include all apps that have models and migrations
APP_MIGRATIONS_PATHS = [
    os.path.join(PROJECT_ROOT, 'accounts', 'migrations'),
    os.path.join(PROJECT_ROOT, 'accounts_amor108', 'migrations'),
    os.path.join(PROJECT_ROOT, 'pools', 'migrations'),
    os.path.join(PROJECT_ROOT, 'governance', 'migrations'),
    os.path.join(PROJECT_ROOT, 'contributions', 'migrations'),
    os.path.join(PROJECT_ROOT, 'profits', 'migrations'),
    os.path.join(PROJECT_ROOT, 'shares', 'migrations'),
    # Add other app migration paths if necessary
]

# List of apps to run makemigrations for
APPS_TO_MAKEMIGRATIONS = [
    'accounts',
    'accounts_amor108',
    'pools',
    'governance',
    'contributions',
    'profits',
    'shares',
    # Add other apps as needed
]

def run_command(command, description):
    print(f"\n--- {description} ---")
    try:
        result = subprocess.run(
            command,
            check=True,
            shell=True,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        print(result.stdout)
        if result.stderr:
            print(f"WARNING: {result.stderr}")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Command failed: {e.cmd}")
        print(f"STDOUT:\n{e.stdout}")
        print(f"STDERR:\n{e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"ERROR: Command not found. Ensure Python and Django are in your PATH and virtual environment is active.")
        sys.exit(1)

def reset_db_and_migrations():
    # 1. Confirm with the user
    confirm = input("This script will DELETE your db.sqlite3 and ALL migration files for specified apps. All data will be lost. Are you sure you want to proceed? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Operation cancelled by user.")
        sys.exit(0)

    # 2. Delete db.sqlite3
    if os.path.exists(DB_FILE):
        print(f"Deleting database file: {DB_FILE}")
        os.remove(DB_FILE)
    else:
        print("Database file not found. Skipping deletion.")

    # 3. Delete migration files
    print("\nDeleting migration files...")
    for path in APP_MIGRATIONS_PATHS:
        if os.path.isdir(path):
            for item in os.listdir(path):
                if item != '__init__.py' and item.endswith('.py'):
                    file_path = os.path.join(path, item)
                    print(f"Deleting migration file: {file_path}")
                    os.remove(file_path)
                elif os.path.isdir(os.path.join(path, item)) and item != '__pycache__':
                    # Also delete migration subdirectories (e.g., __pycache__)
                    shutil.rmtree(os.path.join(path, item))
        else:
            print(f"Migration path not found: {path}")

    # 4. Clear __pycache__
    print("\nCleaning __pycache__ directories...")
    for root, dirs, files in os.walk(PROJECT_ROOT):
        if '__pycache__' in dirs:
            cache_path = os.path.join(root, '__pycache__')
            print(f"Deleting {cache_path}")
            shutil.rmtree(cache_path)

    # 5. Run makemigrations for specified apps
    for app in APPS_TO_MAKEMIGRATIONS:
        run_command(f"python manage.py makemigrations {app}", f"Running makemigrations for {app}")
    
    # 6. Run migrate
    run_command("python manage.py migrate", "Running migrate")

    # 7. Run seed_pools.py
    run_command(f"python {os.path.join(PROJECT_ROOT, 'seed_pools.py')}", "Running seed_pools.py")

    print("\n--- Migration Reset and Database Seeding Complete ---")
    print("You should now be able to start your Django server.")

if __name__ == '__main__':
    reset_db_and_migrations()
