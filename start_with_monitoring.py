"""
Simple launcher to run Django + Resume Monitor together.
Usage: python start_with_monitoring.py
"""

import subprocess
import sys
import time
from pathlib import Path


def run_django_server():
    """Start Django development server."""
    print("🌐 Starting Django server...")
    return subprocess.Popen(
        [sys.executable, 'manage.py', 'runserver'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )


def run_file_monitor():
    """Start resume file monitor."""
    print("👀 Starting file monitor...")
    return subprocess.Popen(
        [
            sys.executable, 'manage.py', 'watch_for_resumes',
            '--folder', 'resumes',
            '--interval', '300',  # 5 minutes
            '--auto-score'
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )


def main():
    print("=" * 80)
    print("🚀 STARTING VOLUNTEER FINDER SYSTEM")
    print("=" * 80)
    print("\nStarting services...")
    print("  • Django Web Server (http://127.0.0.1:8000)")
    print("  • Resume File Monitor (checks every 5 minutes)")
    print("\nPress Ctrl+C to stop both services\n")
    print("=" * 80 + "\n")

    # Start both processes
    django_process = run_django_server()
    time.sleep(2)  # Give Django a moment to start
    monitor_process = run_file_monitor()

    try:
        # Print output from both processes
        while True:
            # Read from Django
            if django_process.poll() is None:  # Still running
                django_line = django_process.stdout.readline()
                if django_line:
                    print(f"[DJANGO] {django_line.strip()}")

            # Read from Monitor
            if monitor_process.poll() is None:  # Still running
                monitor_line = monitor_process.stdout.readline()
                if monitor_line:
                    print(f"[MONITOR] {monitor_line.strip()}")

            # Check if both stopped
            if django_process.poll() is not None and monitor_process.poll() is not None:
                break

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\n" + "=" * 80)
        print("🛑 STOPPING SERVICES...")
        print("=" * 80)

        # Terminate both processes
        django_process.terminate()
        monitor_process.terminate()

        # Wait for clean shutdown
        django_process.wait(timeout=5)
        monitor_process.wait(timeout=5)

        print("✅ All services stopped")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    main()