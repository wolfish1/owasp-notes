import logging
from functools import wraps

from django.db import connection
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .models import Member, Note

# Logger used by the commented-out FLAW 5 fixes (configured in settings.LOGGING).
security_log = logging.getLogger("notes.security")


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def current_member(request):
    member_id = request.session.get("member_id")
    if member_id is None:
        return None
    return Member.objects.filter(pk=member_id).first()


def member_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        member = current_member(request)
        if member is None:
            return redirect("login")
        request.member = member
        return view(request, *args, **kwargs)

    return wrapper


def client_ip(request):
    return request.META.get("REMOTE_ADDR", "?")


# --------------------------------------------------------------------------
# accounts
# --------------------------------------------------------------------------
def register(request):
    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        if not username or not password:
            error = "Username and password are required."
        elif Member.objects.filter(username=username).exists():
            error = "That username is taken."
        else:
            # FLAW 4: Identification and Authentication Failures
            # Any password is accepted ("1", "password", the username itself...).
            # FIX (commented out):
            # from django.contrib.auth.password_validation import validate_password
            # from django.core.exceptions import ValidationError
            # try:
            #     validate_password(password)   # uses settings.AUTH_PASSWORD_VALIDATORS
            # except ValidationError as exc:
            #     return render(request, "notes/register.html",
            #                   {"error": " ".join(exc.messages)})
            member = Member(username=username)
            # FLAW 2: Cryptographic Failures -> set_password() stores plaintext
            # (fix is in notes/models.py, Member.set_password)
            member.set_password(password)
            member.save()
            request.session["member_id"] = member.id
            return redirect("my_notes")
    return render(request, "notes/register.html", {"error": error})


MAX_FAILED_LOGINS = 5
LOCKOUT_SECONDS = 300


def login_view(request):
    error = None
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")

        # FLAW 4: Identification and Authentication Failures
        # Unlimited login attempts: no throttling or lockout, so passwords can
        # be brute-forced with a simple script.
        # FIX (commented out):
        # from django.core.cache import cache
        # lock_key = f"failed-login:{username}:{client_ip(request)}"
        # if cache.get(lock_key, 0) >= MAX_FAILED_LOGINS:
        #     return render(request, "notes/login.html",
        #                   {"error": "Too many failed attempts. Try again in 5 minutes."},
        #                   status=429)

        member = Member.objects.filter(username=username).first()
        if member is not None and member.verify_password(password):
            # FIX (commented out) for FLAW 4: new session id on login, reset counter
            # request.session.cycle_key()
            # cache.delete(lock_key)
            request.session["member_id"] = member.id
            return redirect("my_notes")

        # FLAW 5: Security Logging and Monitoring Failures
        # A failed login is silently ignored - nothing is recorded.
        # FIX (commented out):
        # security_log.warning("Failed login for username=%r from ip=%s",
        #                      username, client_ip(request))
        # FIX (commented out) for FLAW 4: count the failure
        # cache.set(lock_key, cache.get(lock_key, 0) + 1, LOCKOUT_SECONDS)
        error = "Invalid username or password."
    return render(request, "notes/login.html", {"error": error})


def logout_view(request):
    request.session.flush()
    return redirect("public_feed")


# --------------------------------------------------------------------------
# notes
# --------------------------------------------------------------------------
def public_feed(request):
    notes = Note.objects.filter(is_public=True).select_related("owner")
    return render(request, "notes/feed.html",
                  {"notes": notes, "member": current_member(request)})


@member_required
def my_notes(request):
    return render(request, "notes/my_notes.html",
                  {"notes": request.member.notes.all(), "member": request.member})


@member_required
def create_note(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        body = request.POST.get("body", "").strip()
        if title and body:
            Note.objects.create(owner=request.member, title=title, body=body,
                                is_public=bool(request.POST.get("is_public")))
            return redirect("my_notes")
    return render(request, "notes/note_form.html",
                  {"member": request.member, "note": None})


@member_required
def note_detail(request, note_id):
    # FLAW 1: Broken Access Control (IDOR)
    # Any logged-in member can read ANY note (including private ones) just by
    # changing the id in the URL, e.g. /note/1/, /note/2/ ...
    note = get_object_or_404(Note, pk=note_id)
    # FIX (commented out):
    # note = get_object_or_404(Note, pk=note_id)
    # if not note.is_public and note.owner != request.member:
    #     security_log.warning("Access denied: member=%s tried to read note=%s",
    #                          request.member.username, note_id)   # FLAW 5 fix
    #     return HttpResponseForbidden("You do not have access to this note.")
    return render(request, "notes/note_detail.html",
                  {"note": note, "member": request.member})


@member_required
def edit_note(request, note_id):
    # FLAW 1: Broken Access Control (IDOR)
    # The note is looked up only by id, so any member can overwrite someone
    # else's note via /note/<id>/edit/.
    note = get_object_or_404(Note, pk=note_id)
    # FIX (commented out):
    # note = get_object_or_404(Note, pk=note_id)
    # if note.owner != request.member:
    #     security_log.warning("Access denied: member=%s tried to edit note=%s",
    #                          request.member.username, note_id)   # FLAW 5 fix
    #     return HttpResponseForbidden("You can only edit your own notes.")
    if request.method == "POST":
        note.title = request.POST.get("title", note.title).strip()
        note.body = request.POST.get("body", note.body).strip()
        note.is_public = bool(request.POST.get("is_public"))
        note.save()
        return redirect("note_detail", note_id=note.id)
    return render(request, "notes/note_form.html",
                  {"note": note, "member": request.member})


@member_required
def search_notes(request):
    term = request.GET.get("q", "")
    results = []
    if term:
        # FLAW 3: Injection (SQL injection)
        # User input is concatenated straight into the SQL string. Searching
        # for   ' OR 1=1 --   returns every note in the database, private
        # notes of other members included.
        sql = (
            "SELECT id, title, body FROM notes_note "
            "WHERE (owner_id = " + str(request.member.id) + " OR is_public = 1) "
            "AND title LIKE '%" + term + "%'"
        )
        with connection.cursor() as cursor:
            cursor.execute(sql)
            results = [{"id": r[0], "title": r[1], "body": r[2]} for r in cursor.fetchall()]
        # FIX (commented out): parameterised query ...
        # sql = ("SELECT id, title, body FROM notes_note "
        #        "WHERE (owner_id = %s OR is_public = 1) AND title LIKE %s")
        # with connection.cursor() as cursor:
        #     cursor.execute(sql, [request.member.id, f"%{term}%"])
        #     results = [{"id": r[0], "title": r[1], "body": r[2]} for r in cursor.fetchall()]
        # ... or simply the ORM:
        # from django.db.models import Q
        # results = Note.objects.filter(
        #     Q(owner=request.member) | Q(is_public=True), title__icontains=term
        # ).values("id", "title", "body")
    return render(request, "notes/search.html",
                  {"term": term, "results": results, "member": request.member})


@member_required
def moderation(request):
    """Admin area for moderators: overview of all members and notes."""
    if not request.member.is_moderator:
        # FLAW 5: Security Logging and Monitoring Failures
        # Denied access to the admin area is not logged.
        # FIX (commented out):
        # security_log.warning("Access denied: member=%s opened /moderation/ from ip=%s",
        #                      request.member.username, client_ip(request))
        return HttpResponseForbidden("Moderators only.")
    return render(request, "notes/moderation.html", {
        "member": request.member,
        "members": Member.objects.all(),
        "notes": Note.objects.select_related("owner"),
    })
