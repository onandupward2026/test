from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Song(db.Model):
    """Songs in the library."""
    __tablename__ = "songs"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    artist = db.Column(db.String(200))
    key = db.Column(db.String(20))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    set_list_items = db.relationship("SetListItem", back_populates="song", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Song {self.title}>"


class CastMember(db.Model):
    """Roster of performers."""
    __tablename__ = "cast_members"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(100))  # vocals, keys, guitar, bass, drums, etc.
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    notes = db.Column(db.Text)

    event_assignments = db.relationship("EventCast", back_populates="cast_member", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CastMember {self.name}>"


class Event(db.Model):
    """A service or performance event."""
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    # "big_crush" = Monday Big Crush, "hip_service" = Wednesday Hip Service
    service_type = db.Column(db.String(50), nullable=False)
    venue = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    set_list_items = db.relationship(
        "SetListItem", back_populates="event",
        cascade="all, delete-orphan",
        order_by="SetListItem.position"
    )
    cast_assignments = db.relationship(
        "EventCast", back_populates="event",
        cascade="all, delete-orphan"
    )
    rehearsals = db.relationship(
        "Rehearsal", back_populates="event",
        cascade="all, delete-orphan",
        order_by="Rehearsal.rehearsal_date"
    )

    @property
    def service_label(self):
        return "Monday Big Crush" if self.service_type == "big_crush" else "Wednesday Hip Service"

    @property
    def rehearsal_day(self):
        return "Monday" if self.service_type == "big_crush" else "Wednesday"

    def __repr__(self):
        return f"<Event {self.name} on {self.event_date}>"


class SetListItem(db.Model):
    """An ordered song in an event's set list."""
    __tablename__ = "set_list_items"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey("songs.id"), nullable=False)
    position = db.Column(db.Integer, nullable=False, default=1)
    notes = db.Column(db.Text)  # e.g. "extended intro", "key change"

    event = db.relationship("Event", back_populates="set_list_items")
    song = db.relationship("Song", back_populates="set_list_items")

    def __repr__(self):
        return f"<SetListItem {self.position}: {self.song.title}>"


class EventCast(db.Model):
    """A cast member assigned to a specific event."""
    __tablename__ = "event_cast"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    cast_member_id = db.Column(db.Integer, db.ForeignKey("cast_members.id"), nullable=False)
    role_override = db.Column(db.String(100))  # Override default role for this event

    event = db.relationship("Event", back_populates="cast_assignments")
    cast_member = db.relationship("CastMember", back_populates="event_assignments")
    sub = db.relationship("Sub", back_populates="event_cast", uselist=False, cascade="all, delete-orphan")

    @property
    def effective_role(self):
        return self.role_override or self.cast_member.role

    def __repr__(self):
        return f"<EventCast {self.cast_member.name} @ {self.event.name}>"


class Sub(db.Model):
    """A substitute replacing a cast member for a specific event assignment."""
    __tablename__ = "subs"

    id = db.Column(db.Integer, primary_key=True)
    event_cast_id = db.Column(db.Integer, db.ForeignKey("event_cast.id"), nullable=False)
    sub_name = db.Column(db.String(200), nullable=False)
    sub_contact = db.Column(db.String(200))  # phone or email
    confirmed = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)

    event_cast = db.relationship("EventCast", back_populates="sub")

    def __repr__(self):
        return f"<Sub {self.sub_name} for {self.event_cast.cast_member.name}>"


class Rehearsal(db.Model):
    """A rehearsal session linked to an event."""
    __tablename__ = "rehearsals"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    rehearsal_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.String(10))   # e.g. "6:30 PM"
    end_time = db.Column(db.String(10))     # e.g. "9:00 PM"
    location = db.Column(db.String(200))
    focus_notes = db.Column(db.Text)        # What to focus on this rehearsal
    agenda = db.Column(db.Text)             # Free-form agenda notes

    event = db.relationship("Event", back_populates="rehearsals")

    @property
    def day_of_week(self):
        return self.rehearsal_date.strftime("%A")

    def __repr__(self):
        return f"<Rehearsal {self.rehearsal_date} for {self.event.name}>"
