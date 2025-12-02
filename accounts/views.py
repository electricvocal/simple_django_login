import re
from django.shortcuts import render, redirect
from django.http import HttpResponse
from pathlib import Path
from django.conf import settings

USERS_FILE = Path(settings.BASE_DIR) / "users.txt"

# Regex used to parse lines like: (username, email, password, subscription)
USER_REGEX = re.compile(r'\(\s*(?P<username>[^,]+)\s*,\s*(?P<email>[^,]+)\s*,\s*(?P<password>[^,]+)\s*,\s*(?P<sub>[^)]+)\s*\)')

def ensure_users_file():
    if not USERS_FILE.exists():
        USERS_FILE.write_text("")

def parse_user_line(line):
    m = USER_REGEX.search(line)
    if not m:
        return None
    return {
        "username": m.group("username").strip().strip('"').strip("'"),
        "email": m.group("email").strip().strip('"').strip("'"),
        "password": m.group("password").strip().strip('"').strip("'"),
        "subscription": m.group("sub").strip().strip('"').strip("'"),
    }

def read_all_users():
    ensure_users_file()
    users = []
    for line in USERS_FILE.read_text(encoding='utf-8').splitlines():
        parsed = parse_user_line(line)
        if parsed:
            users.append(parsed)
    return users

def append_user(username, email, password, subscription="basic"):
    ensure_users_file()
    # write in exact tuple-like format, fields as entered
    line = f"({username}, {email}, {password}, {subscription})\n"
    with open(USERS_FILE, "a", encoding="utf-8") as f:
        f.write(line)

def home(request):
    return redirect("login")

def register_view(request):
    message = ""
    if request.method == "POST":
        username = request.POST.get("username","").strip()
        email = request.POST.get("email","").strip()
        password = request.POST.get("password","").strip()
        if not username or not email or not password:
            message = "Todos los campos son obligatorios."
        else:
            # simple duplicate check by username or email
            users = read_all_users()
            dup = next((u for u in users if u["username"]==username or u["email"]==email), None)
            if dup:
                message = "El usuario o email ya existe."
            else:
                append_user(username, email, password, "basic")
                message = "Registro exitoso. Ahora puedes ingresar."
                return render(request, "register.html", {"message": message, "success": True})
    return render(request, "register.html", {"message": message})

def login_view(request):
    message = ""
    if request.method == "POST":
        identifier = request.POST.get("identifier","").strip()
        password = request.POST.get("password","").strip()
        users = read_all_users()
        found = None
        for u in users:
            if (u["username"] == identifier or u["email"] == identifier) and u["password"] == password:
                found = u
                break
        if found:
            # set session
            request.session['username'] = found["username"]
            request.session['subscription'] = found["subscription"]
            return redirect("dashboard")
        else:
            message = "Credenciales inválidas."
    return render(request, "login.html", {"message": message})

def dashboard(request):
    username = request.session.get("username")
    subscription = request.session.get("subscription")
    if not username:
        return redirect("login")
    if subscription == "pro":
        msg = "Eres PRO!"
    else:
        msg = "Eres BASIC!"
    return render(request, "dashboard.html", {"username": username, "message": msg})

def logout_view(request):
    request.session.flush()
    return redirect("login")
