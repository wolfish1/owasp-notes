from django.db import migrations

# Demo data so reviewers can start testing right after `migrate`.
# Passwords are stored the same way the (flawed) Member model stores them:
# plaintext. If you enable the FLAW 2 fix, reset them with set_password().

def seed(apps, schema_editor):
    Member = apps.get_model("notes", "Member")
    Note = apps.get_model("notes", "Note")
    alice, _ = Member.objects.get_or_create(
        username="alice", defaults={"password": "1", "is_moderator": True})
    bob, _ = Member.objects.get_or_create(
        username="bob", defaults={"password": "1"})
    if not Note.objects.exists():
        Note.objects.create(owner=alice, title="Alice private secret",
                            body="Only Alice should see this secret note.", is_public=False)
        Note.objects.create(owner=alice, title="Alice public hello",
                            body="Hello from Alice.", is_public=True)
        Note.objects.create(owner=bob, title="Bob private plan",
                            body="Bob private content.", is_public=False)


def unseed(apps, schema_editor):
    Member = apps.get_model("notes", "Member")
    Member.objects.filter(username__in=["alice", "bob"]).delete()


class Migration(migrations.Migration):
    dependencies = [("notes", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
