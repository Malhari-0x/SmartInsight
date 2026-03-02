"""
WSGI config for smartinsight project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

# Ensure Django project root is importable when running from repository root on Vercel.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartinsight.settings')

# For demo deployments without DATABASE_URL, initialize writable sqlite in /tmp.
if os.getenv("VERCEL") and not os.getenv("DATABASE_URL"):
    db_file = Path("/tmp/db.sqlite3")
    if not db_file.exists():
        import django
        from django.core.management import call_command

        django.setup()
        call_command("migrate", interactive=False, verbosity=0, run_syncdb=True)
        call_command(
            "seed_demo_user",
            username="User",
            password="User@1234",
            verbosity=0,
        )

application = get_wsgi_application()
