"""
Pytest configuration and fixtures for Playwright e2e tests.
"""
import os
import pytest
import subprocess
import socket
import time


def get_free_port():
    """Get a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


@pytest.fixture(scope="session")
def django_server():
    """Start Django development server for e2e tests using a test database."""
    port = get_free_port()
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_db_path = os.path.join(project_root, 'test_db.sqlite3')

    # Set environment variables for test database
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = 'volunteer_finder.settings'
    env['TEST_DATABASE'] = test_db_path

    # Remove old test database if it exists
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    # Run migrations on the test database
    migrate_process = subprocess.run(
        ['python', 'manage.py', 'migrate', '--run-syncdb'],
        env=env,
        cwd=project_root,
        capture_output=True,
        text=True
    )
    if migrate_process.returncode != 0:
        raise RuntimeError(f"Migration failed: {migrate_process.stderr}")

    # Create test users using a management command or direct script
    setup_script = """
import django
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'volunteer_finder.settings'
os.environ['TEST_DATABASE'] = '{test_db_path}'
django.setup()

from accounts.models import User, VolunteerProfile

# Create a verified volunteer user
if not User.objects.filter(username='testvolunteer').exists():
    user = User.objects.create_user(
        username='testvolunteer',
        email='testvolunteer@example.com',
        password='TestPass123!',
        user_type='volunteer',
        email_verified=True,
        first_name='Test',
        last_name='Volunteer'
    )
    VolunteerProfile.objects.create(user=user)
    print('Created test volunteer user')

# Create an unverified volunteer user
if not User.objects.filter(username='unverifiedvolunteer').exists():
    user = User.objects.create_user(
        username='unverifiedvolunteer',
        email='unverified@example.com',
        password='TestPass123!',
        user_type='volunteer',
        email_verified=False,
        first_name='Unverified',
        last_name='User'
    )
    VolunteerProfile.objects.create(user=user)
    print('Created unverified volunteer user')

print('Test users setup complete')
""".format(test_db_path=test_db_path)

    setup_process = subprocess.run(
        ['python', '-c', setup_script],
        env=env,
        cwd=project_root,
        capture_output=True,
        text=True
    )
    if setup_process.returncode != 0:
        raise RuntimeError(f"Test user setup failed: {setup_process.stderr}")

    # Start the Django development server with test database
    process = subprocess.Popen(
        ['python', 'manage.py', 'runserver', f'127.0.0.1:{port}', '--noreload'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=project_root
    )

    # Wait for the server to start
    max_wait = 30
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('127.0.0.1', port))
                break
        except ConnectionRefusedError:
            time.sleep(0.5)
    else:
        process.kill()
        raise RuntimeError("Django server failed to start")

    yield f"http://127.0.0.1:{port}"

    # Cleanup: terminate the server and remove test database
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()

    # Remove test database
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context options."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
    }


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """Configure browser launch options."""
    return {
        **browser_type_launch_args,
        "headless": True,
    }
