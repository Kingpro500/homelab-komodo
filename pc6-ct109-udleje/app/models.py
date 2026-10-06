"""Domænemodeller for udlejningsformidlingen.

En formidler ejer ikke boligerne - en *udlejer* (landlord) opretter sine
boliger, en *admin* godkender dem til offentlig visning, og en *lejer*
(interessent) sender en henvendelse gennem formularen på boligsiden.
"""
from datetime import datetime, date

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "brugere"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    navn = db.Column(db.String(255), nullable=False)
    telefon = db.Column(db.String(40), default="")
    rolle = db.Column(db.String(20), nullable=False, default="udlejer")  # udlejer | admin
    aktiv = db.Column(db.Boolean, nullable=False, default=True)
    oprettet = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    boliger = db.relationship("Bolig", backref="ejer", lazy="dynamic")

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)

    def er_admin(self):
        return self.rolle == "admin"


class Bolig(db.Model):
    __tablename__ = "boliger"

    id = db.Column(db.Integer, primary_key=True)
    ejer_id = db.Column(db.Integer, db.ForeignKey("brugere.id"), nullable=False, index=True)

    overskrift = db.Column(db.String(200), nullable=False)
    beskrivelse = db.Column(db.Text, default="")

    boligtype = db.Column(db.String(30), default="lejlighed")  # hus | lejlighed | andet
    adresse = db.Column(db.String(200), default="")
    postnr = db.Column(db.String(10), default="")
    by = db.Column(db.String(120), default="")
    kommune = db.Column(db.String(120), default="", index=True)

    areal_m2 = db.Column(db.Integer, default=0)
    vaerelser = db.Column(db.Integer, default=0)
    moebleret = db.Column(db.Boolean, nullable=False, default=False)

    husleje_pr_maaned = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    depositum = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    forudbetalt = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    ledig_fra = db.Column(db.Date, default=date.today)

    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    # udkast -> (admin godkender) -> aktiv -> udlejet/afvist
    status = db.Column(db.String(20), nullable=False, default="udkast", index=True)

    oprettet = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    opdateret = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    billeder = db.relationship(
        "Billede",
        backref="bolig",
        lazy="select",
        order_by="Billede.sort_index",
        cascade="all, delete-orphan",
    )
    henvendelser = db.relationship(
        "Henvendelse",
        backref="bolig",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    @property
    def hovedbillede(self):
        for b in self.billeder:
            if b.er_forside:
                return b
        return self.billeder[0] if self.billeder else None

    @property
    def har_kort(self):
        return self.latitude is not None and self.longitude is not None

    @property
    def husleje_vis(self):
        return _fmt_kr(self.husleje_pr_maaned)

    @property
    def depositum_vis(self):
        return _fmt_kr(self.depositum)

    @property
    def forudbetalt_vis(self):
        return _fmt_kr(self.forudbetalt)


class Billede(db.Model):
    __tablename__ = "billeder"

    id = db.Column(db.Integer, primary_key=True)
    bolig_id = db.Column(db.Integer, db.ForeignKey("boliger.id"), nullable=False)
    filnavn = db.Column(db.String(255), nullable=False)
    sort_index = db.Column(db.Integer, default=0)
    er_forside = db.Column(db.Boolean, nullable=False, default=False)


class Henvendelse(db.Model):
    __tablename__ = "henvendelser"

    id = db.Column(db.Integer, primary_key=True)
    bolig_id = db.Column(db.Integer, db.ForeignKey("boliger.id"), nullable=False, index=True)
    navn = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    telefon = db.Column(db.String(40), default="")
    besked = db.Column(db.Text, default="")
    laest = db.Column(db.Boolean, nullable=False, default=False)
    oprettet = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @property
    def oprettet_vis(self):
        return self.oprettet.strftime("%d. %b %Y %H:%M")


def _fmt_kr(v):
    if v is None:
        return "0 kr."
    return f"{int(round(float(v))):,} kr.".replace(",", ".")
