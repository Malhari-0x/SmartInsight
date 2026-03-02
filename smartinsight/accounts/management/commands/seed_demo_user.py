import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update demo credentials for testing."

    def add_arguments(self, parser):
        parser.add_argument("--username", default=os.getenv("DEMO_USERNAME", "User"))
        parser.add_argument("--password", default=os.getenv("DEMO_PASSWORD", "User@1234"))
        parser.add_argument("--email", default=os.getenv("DEMO_EMAIL", "user@example.com"))
        parser.add_argument(
            "--company-name",
            dest="company_name",
            default=os.getenv("DEMO_COMPANY_NAME", "Demo Company"),
        )
        parser.add_argument("--role", default=os.getenv("DEMO_ROLE", "tester"))
        parser.add_argument(
            "--subscription-type",
            dest="subscription_type",
            default=os.getenv("DEMO_SUBSCRIPTION_TYPE", "free"),
        )

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]
        email = options["email"]
        company_name = options["company_name"]
        role = options["role"]
        subscription_type = options["subscription_type"]

        User = get_user_model()
        model_field_names = {field.name for field in User._meta.fields}

        defaults = {}
        if "email" in model_field_names:
            defaults["email"] = email
        if "company_name" in model_field_names:
            defaults["company_name"] = company_name
        if "role" in model_field_names:
            defaults["role"] = role
        if "subscription_type" in model_field_names:
            defaults["subscription_type"] = subscription_type

        user, created = User.objects.get_or_create(username=username, defaults=defaults)
        changed = created

        for field_name, field_value in defaults.items():
            if getattr(user, field_name, None) != field_value:
                setattr(user, field_name, field_value)
                changed = True

        if not user.is_active:
            user.is_active = True
            changed = True

        if not user.check_password(password):
            user.set_password(password)
            changed = True

        if changed:
            user.save()

        self.stdout.write(
            self.style.SUCCESS(f"Demo user ready: username='{username}'")
        )
