from django.db import models


class Member(models.Model):
    """Custom user table used by the notes app (separate from django.contrib.auth)."""

    username = models.CharField(max_length=60, unique=True)
    # FLAW 2: Cryptographic Failures
    # The password column holds the raw password exactly as typed (plaintext).
    password = models.CharField(max_length=128)
    # (Fix note: the column keeps its size; after the fix it stores a PBKDF2
    #  hash from make_password() - see the commented FIX below.)
    is_moderator = models.BooleanField(default=False)
    joined = models.DateTimeField(auto_now_add=True)

    # FLAW 2 (continued): password is stored / compared as plaintext.
    def set_password(self, raw_password):
        self.password = raw_password

    def verify_password(self, raw_password):
        return self.password == raw_password

    # FIX (commented out):
    # def set_password(self, raw_password):
    #     from django.contrib.auth.hashers import make_password
    #     self.password = make_password(raw_password)
    #
    # def verify_password(self, raw_password):
    #     from django.contrib.auth.hashers import check_password
    #     return check_password(raw_password, self.password)

    def __str__(self):
        return self.username


class Note(models.Model):
    owner = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="notes")
    title = models.CharField(max_length=120)
    body = models.TextField()
    is_public = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.title
