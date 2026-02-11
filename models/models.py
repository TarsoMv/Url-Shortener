from extensions import db
from datetime import datetime

class User(db.Model):
    __tablename__ = "USERS"

    id = db.Column("UserID", db.Integer, primary_key=True)
    username = db.Column("UserName", db.String(255), nullable=False)
    password_hash = db.Column("PasswordHash", db.String(255), nullable=False)
    email = db.Column("Email", db.String(255), unique=True)

    sites = db.relationship(
        "Site",
        back_populates="user",
        passive_deletes=True
    )


class Site(db.Model):
    __tablename__ = "SITES"

    url_short = db.Column("UrlShort", db.String(15), primary_key=True)
    full_url = db.Column("FullUrl", db.String(255), nullable=False)

    user_id = db.Column(
        "UserID",
        db.Integer,
        db.ForeignKey("USERS.UserID", ondelete="CASCADE"),
        nullable=False
    )

    user = db.relationship("User", back_populates="sites")

    accesses = db.relationship(
        "Access",
        back_populates="site",
        passive_deletes=True
    )

class Access(db.Model):
    __tablename__ = "ACCESS"

    id = db.Column("AccessID", db.Integer, primary_key=True)

    url_short = db.Column(
        "UrlShort",
        db.String(15),
        db.ForeignKey("SITES.UrlShort", ondelete="CASCADE"),
        nullable=False
    )

    access_datetime = db.Column(
        "AccessDateTime",
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    ip_address = db.Column("IPAddress", db.String(45))

    site = db.relationship("Site", back_populates="accesses")