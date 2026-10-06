"""Udlejning - formidlingsportal (MVP).

Lille skræddersyet Flask-app: udlejere opretter boliger, admin godkender,
offentligheden søger og sender henvendelser. Roller: udlejer / admin.
"""
import os
import secrets
from functools import wraps

from flask import (
    Flask, g, session, request, redirect, url_for, flash, render_template,
    abort, send_from_directory,
)
from werkzeug.utils import secure_filename

from .models import db, User, Bolig, Billede, Henvendelse


ALLOWED_BILEDER = {"jpg", "jpeg", "png", "webp"}
MAX_BILEDE_MB = 8
STATUS_LABEL = {
    "udkast": "Udkast",
    "aktiv": "Aktiv",
    "udlejet": "Udlejet",
    "afvist": "Afvist",
}


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", secrets.token_hex(32)),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", "sqlite:///" + os.path.join(app.instance_path, "udleje.sqlite")
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.environ.get("UPLOAD_FOLDER", os.path.join(app.instance_path, "uploads")),
        MAX_CONTENT_LENGTH=20 * 1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)

    # ---------- auth-hjælpere ----------
    def _login_bruger(bruger):
        session.clear()
        session["user_id"] = bruger.id
        session["csrf"] = secrets.token_hex(16)
        session.permanent = True

    @app.before_request
    def _sæt_g():
        g.bruger = None
        uid = session.get("user_id")
        if uid:
            g.bruger = db.session.get(User, uid)
        # CSRF-token skal findes allerede ved første besøg, ellers er alle
        # formularer døde indtil login. Opret den her hvis den mangler.
        if not session.get("csrf"):
            session["csrf"] = secrets.token_hex(16)
        g.csrf = session.get("csrf")

    def login_påkrævet(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if g.bruger is None:
                flash("Log ind for at fortsætte.", "advarsel")
                return redirect(url_for("login", næste=request.path))
            return fn(*args, **kwargs)
        return wrapper

    def admin_påkrævet(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if g.bruger is None or not g.bruger.er_admin():
                abort(403)
            return fn(*args, **kwargs)
        return wrapper

    def csrf_ok():
        # Token fra skjemaet skal matche session-token.
        return request.form.get("csrf") == session.get("csrf")

    def csrf_krævet(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if request.method == "POST" and not csrf_ok():
                abort(400, "Ugyldig CSRF-token.")
            return fn(*args, **kwargs)
        return wrapper

    app.jinja_env.globals["status_label"] = lambda s: STATUS_LABEL.get(s, s)

    # ---------- offentlige sider ----------
    @app.route("/")
    def index():
        query = Bolig.query.filter_by(status="aktiv")

        kommune = request.args.get("kommune", "").strip()
        type_ = request.args.get("type", "").strip()
        max_pris = request.args.get("max_pris", "").strip()
        min_vaer = request.args.get("min_vaerelser", "").strip()

        if kommune:
            query = query.filter(Bolig.kommune.ilike(f"%{kommune}%"))
        if type_:
            query = query.filter(Bolig.boligtype == type_)
        if max_pris:
            try:
                query = query.filter(Bolig.husleje_pr_maaned <= int(max_pris))
            except ValueError:
                pass
        if min_vaer:
            try:
                query = query.filter(Bolig.vaerelser >= int(min_vaer))
            except ValueError:
                pass

        sorter = request.args.get("sorter", "nyeste")
        if sorter == "pris_lav":
            query = query.order_by(Bolig.husleje_pr_maaned.asc())
        elif sorter == "pris_høj":
            query = query.order_by(Bolig.husleje_pr_maaned.desc())
        else:
            query = query.order_by(Bolig.oprettet.desc())

        kommunevalg = sorted(
            k[0] for k in db.session.query(Bolig.kommune)
            .filter(Bolig.kommune != "", Bolig.status == "aktiv")
            .distinct().all() if k[0]
        )

        boliger = query.limit(60).all()
        return render_template(
            "index.html", boliger=boliger, kommunevalg=kommunevalg,
            f={k: v for k, v in request.args.items()},
        )

    @app.route("/bolig/<int:b_id>")
    def bolig_side(b_id):
        bolig = db.session.get(Bolig, b_id)
        if bolig is None or bolig.status != "aktiv":
            abort(404)
        return render_template("bolig.html", bolig=bolig)

    @app.route("/bolig/<int:b_id>/henvendelse", methods=["POST"])
    @csrf_krævet
    def henvendelse(b_id):
        bolig = db.session.get(Bolig, b_id)
        if bolig is None or bolig.status != "aktiv":
            abort(404)
        navn = request.form.get("navn", "").strip()
        email = request.form.get("email", "").strip()
        if not navn or "@" not in email:
            flash("Udfyld navn og en gyldig e-mail.", "advarsel")
            return redirect(url_for("bolig_side", b_id=b_id))
        h = Henvendelse(
            bolig=bolig, navn=navn, email=email,
            telefon=request.form.get("telefon", "").strip(),
            besked=request.form.get("besked", "").strip(),
        )
        db.session.add(h)
        db.session.commit()
        flash("Tak! Din henvendelse er sendt til udlejer.", "succes")
        return redirect(url_for("bolig_side", b_id=b_id))

    @app.route("/om")
    def om():
        return render_template("om.html")

    # ---------- auth ----------
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            if not csrf_ok():
                abort(400)
            email = request.form.get("email", "").strip().lower()
            pw = request.form.get("password", "")
            bruger = User.query.filter_by(email=email).first()
            if bruger and bruger.aktiv and bruger.check_password(pw):
                _login_bruger(bruger)
                flash("Velkommen tilbage.", "succes")
                næste = request.args.get("næste")
                return redirect(næste or url_for("portal"))
            flash("Forkert e-mail eller adgangskode.", "advarsel")
        return render_template("login.html")

    @app.route("/registrer", methods=["GET", "POST"])
    def registrer():
        if g.bruger:
            return redirect(url_for("portal"))
        if request.method == "POST":
            if not csrf_ok():
                abort(400)
            navn = request.form.get("navn", "").strip()
            email = request.form.get("email", "").strip().lower()
            pw = request.form.get("password", "")
            if not navn or "@" not in email or len(pw) < 8:
                flash("Udfyld alle felter (adgangskode mindst 8 tegn).", "advarsel")
            elif User.query.filter_by(email=email).first():
                flash("Der findes allerede en konto med den e-mail.", "advarsel")
            else:
                b = User(email=email, navn=navn,
                         telefon=request.form.get("telefon", "").strip(), rolle="udlejer")
                b.set_password(pw)
                db.session.add(b)
                db.session.commit()
                _login_bruger(b)
                flash("Konto oprettet. Velkommen!", "succes")
                return redirect(url_for("portal"))
        return render_template("registrer.html")

    @app.route("/logout", methods=["POST"])
    @csrf_krævet
    def logout():
        session.clear()
        return redirect(url_for("index"))

    # ---------- udlejer-portal ----------
    @app.route("/portal")
    @login_påkrævet
    def portal():
        boliger = Bolig.query.filter_by(ejer_id=g.bruger.id).order_by(Bolig.oprettet.desc()).all()
        return render_template("portal/index.html", boliger=boliger)

    @app.route("/portal/ny", methods=["GET", "POST"])
    @login_påkrævet
    @csrf_krævet
    def ny_bolig():
        if request.method == "POST":
            b = _byg_bolig_fra_form(Bolig(ejer_id=g.bruger.id))
            db.session.add(b)
            db.session.commit()
            _gem_billeder(b)
            flash("Bolig oprettet. Den vises offentligt, når admin har godkendt den.", "succes")
            return redirect(url_for("portal"))
        return render_template("portal/rediger.html", bolig=None, status_label=STATUS_LABEL)

    @app.route("/portal/<int:b_id>/rediger", methods=["GET", "POST"])
    @login_påkrævet
    @csrf_krævet
    def rediger_bolig(b_id):
        b = _ejet_bolig(b_id)
        if request.method == "POST":
            b = _byg_bolig_fra_form(b)
            db.session.commit()
            _gem_billeder(b)
            flash("Ændringer gemt.", "succes")
            return redirect(url_for("portal"))
        return render_template("portal/rediger.html", bolig=b, status_label=STATUS_LABEL)

    @app.route("/portal/<int:b_id>/slet", methods=["POST"])
    @login_påkrævet
    @csrf_krævet
    def slet_bolig(b_id):
        b = _ejet_bolig(b_id)
        for billede in b.billeder:
            _slet_fil(billede.filnavn)
        db.session.delete(b)
        db.session.commit()
        flash("Bolig slettet.", "succes")
        return redirect(url_for("portal"))

    @app.route("/portal/<int:b_id>/slet-billede/<int:bi_id>", methods=["POST"])
    @login_påkrævet
    @csrf_krævet
    def slet_billede(b_id, bi_id):
        b = _ejet_bolig(b_id)
        billede = db.session.get(Billede, bi_id)
        if billede and billede.bolig_id == b.id:
            _slet_fil(billede.filnavn)
            db.session.delete(billede)
            db.session.commit()
            flash("Billede fjernet.", "succes")
        return redirect(url_for("rediger_bolig", b_id=b.id))

    @app.route("/portal/<int:b_id>/henvendelser")
    @login_påkrævet
    def henvendelser(b_id):
        b = _ejet_bolig(b_id)
        henvendelser = b.henvendelser.order_by(Henvendelse.oprettet.desc()).all()
        return render_template("portal/henvendelser.html", bolig=b, henvendelser=henvendelser)

    @app.route("/portal/henvendelser/mark-laest/<int:h_id>", methods=["POST"])
    @login_påkrævet
    @csrf_krævet
    def mark_laest(h_id):
        h = db.session.get(Henvendelse, h_id)
        if h and h.bolig.ejer_id == g.bruger.id:
            h.laest = True
            db.session.commit()
        return redirect(url_for("henvendelser", b_id=h.bolig_id))

    # ---------- admin ----------
    @app.route("/admin")
    @admin_påkrævet
    def admin():
        boliger = Bolig.query.order_by(Bolig.oprettet.desc()).all()
        brugere = User.query.order_by(User.oprettet.desc()).all()
        return render_template("admin/index.html", boliger=boliger, brugere=brugere,
                               status_items=list(STATUS_LABEL.items()))

    @app.route("/admin/bolig/<int:b_id>/status", methods=["POST"])
    @admin_påkrævet
    @csrf_krævet
    def admin_status(b_id):
        b = db.session.get(Bolig, b_id)
        if b:
            ny = request.form.get("status")
            if ny in STATUS_LABEL:
                b.status = ny
                db.session.commit()
                flash(f"Status sat til «{STATUS_LABEL[ny]}».", "succes")
        return redirect(url_for("admin"))

    @app.route("/admin/bruger/<int:u_id>/toggle", methods=["POST"])
    @admin_påkrævet
    @csrf_krævet
    def admin_bruger_toggle(u_id):
        u = db.session.get(User, u_id)
        if u and u.id != g.bruger.id:
            u.aktiv = not u.aktiv
            db.session.commit()
            flash("Bruger opdateret.", "succes")
        return redirect(url_for("admin"))

    # ---------- uploadede billeder ----------
    @app.route("/uploads/<path:filnavn>")
    def uploads(filnavn):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filnavn)

    # ---------- init-db ----------
    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        email = os.environ.get("ADMIN_EMAIL", "admin@udleje.local").lower()
        if User.query.filter_by(email=email).first() is None:
            admin = User(email=email, navn="Admin", rolle="admin", aktiv=True)
            admin.set_password(os.environ.get("ADMIN_PASSWORD", "skift-mig"))
            db.session.add(admin)
            db.session.commit()
            print(f"Admin oprettet: {email}")
        print("Database klar.")

    # ---------- interne hjælpere ----------
    def _ejet_bolig(b_id):
        b = db.session.get(Bolig, b_id)
        if b is None or b.ejer_id != g.bruger.id:
            abort(404)
        return b

    def _byg_bolig_fra_form(b):
        b.overskrift = request.form.get("overskrift", "").strip()[:200]
        b.beskrivelse = request.form.get("beskrivelse", "").strip()
        b.boligtype = request.form.get("boligtype", "lejlighed")
        b.adresse = request.form.get("adresse", "").strip()
        b.postnr = request.form.get("postnr", "").strip()
        b.by = request.form.get("by", "").strip()
        b.kommune = request.form.get("kommune", "").strip()
        b.areal_m2 = _int_felt("areal_m2")
        b.vaerelser = _int_felt("vaerelser")
        b.moebleret = request.form.get("moebleret") == "on"
        b.husleje_pr_maaned = _beløb_felt("husleje")
        b.depositum = _beløb_felt("depositum")
        b.forudbetalt = _beløb_felt("forudbetalt")
        b.ledig_fra = _dato_felt("ledig_fra")
        b.latitude = _float_felt("latitude")
        b.longitude = _float_felt("longitude")
        return b

    def _gem_billeder(b):
        filer = request.files.getlist("billeder")
        nye = [f for f in filer if f and f.filename]
        if not nye:
            return
        start = len(b.billeder)
        for i, fil in enumerate(nye):
            navn = secure_filename(fil.filename)
            ext = navn.rsplit(".", 1)[-1].lower() if "." in navn else ""
            if ext not in ALLOWED_BILEDER:
                flash(f"«{fil.filename}» er ikke et billede (jpg/png/webp).", "advarsel")
                continue
            gemt = f"b{b.id}_{secrets.token_hex(6)}.{ext}"
            fil.save(os.path.join(app.config["UPLOAD_FOLDER"], gemt))
            db.session.add(Billede(
                bolig_id=b.id, filnavn=gemt, sort_index=start + i,
                er_forside=len(b.billeder) == 0 and i == 0,
            ))
        db.session.commit()

    def _slet_fil(filnavn):
        try:
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], filnavn))
        except OSError:
            pass

    def _int_felt(felt):
        try:
            return int(request.form.get(felt, "") or 0)
        except ValueError:
            return 0

    def _beløb_felt(felt):
        v = request.form.get(felt, "").strip().replace(".", "").replace(",", ".")
        try:
            return float(v) if v else 0.0
        except ValueError:
            return 0.0

    def _float_felt(felt):
        v = request.form.get(felt, "").strip().replace(",", ".")
        try:
            return float(v) if v else None
        except ValueError:
            return None

    def _dato_felt(felt):
        from datetime import datetime as _dt
        v = request.form.get(felt, "").strip()
        try:
            return _dt.strptime(v, "%Y-%m-%d").date()
        except ValueError:
            return None

    return app
