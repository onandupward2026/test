import os
from datetime import date, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from models import db, Event, Song, CastMember, SetListItem, EventCast, Sub, Rehearsal

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///rehearsal.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def next_weekday(from_date: date, weekday: int) -> date:
    """Return the nearest upcoming weekday (0=Mon … 6=Sun) on or after from_date."""
    days_ahead = weekday - from_date.weekday()
    if days_ahead < 0:
        days_ahead += 7
    return from_date + timedelta(days=days_ahead)


def suggest_rehearsal_date(event_date: date, service_type: str) -> date:
    """Suggest a rehearsal date: preceding Monday (big_crush) or Wednesday (hip_service)."""
    target_weekday = 0 if service_type == "big_crush" else 2  # 0=Mon, 2=Wed
    # Go back to find the preceding target weekday before event_date
    candidate = event_date - timedelta(days=1)
    while candidate.weekday() != target_weekday:
        candidate -= timedelta(days=1)
    return candidate


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    today = date.today()
    upcoming = (
        Event.query
        .filter(Event.event_date >= today)
        .order_by(Event.event_date)
        .all()
    )
    past = (
        Event.query
        .filter(Event.event_date < today)
        .order_by(Event.event_date.desc())
        .limit(5)
        .all()
    )
    return render_template("index.html", upcoming=upcoming, past=past, today=today)


# ─────────────────────────────────────────────────────────────────────────────
# Events
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/events/new", methods=["GET", "POST"])
def event_new():
    if request.method == "POST":
        event_date = date.fromisoformat(request.form["event_date"])
        service_type = request.form["service_type"]
        event = Event(
            name=request.form["name"].strip(),
            event_date=event_date,
            service_type=service_type,
            venue=request.form.get("venue", "").strip(),
            notes=request.form.get("notes", "").strip(),
        )
        db.session.add(event)
        db.session.flush()  # get event.id before adding rehearsal

        # Auto-create a suggested rehearsal
        suggested = suggest_rehearsal_date(event_date, service_type)
        rehearsal = Rehearsal(
            event_id=event.id,
            rehearsal_date=suggested,
            start_time="6:30 PM",
            end_time="9:00 PM",
            location=event.venue or "",
        )
        db.session.add(rehearsal)
        db.session.commit()
        flash("Event created! A rehearsal has been auto-scheduled.", "success")
        return redirect(url_for("event_detail", event_id=event.id))

    return render_template("event_form.html", event=None)


@app.route("/events/<int:event_id>")
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    all_songs = Song.query.order_by(Song.title).all()
    all_cast = CastMember.query.order_by(CastMember.name).all()
    assigned_song_ids = {item.song_id for item in event.set_list_items}
    assigned_cast_ids = {ec.cast_member_id for ec in event.cast_assignments}
    return render_template(
        "event_detail.html",
        event=event,
        all_songs=all_songs,
        all_cast=all_cast,
        assigned_song_ids=assigned_song_ids,
        assigned_cast_ids=assigned_cast_ids,
    )


@app.route("/events/<int:event_id>/edit", methods=["GET", "POST"])
def event_edit(event_id):
    event = Event.query.get_or_404(event_id)
    if request.method == "POST":
        event.name = request.form["name"].strip()
        event.event_date = date.fromisoformat(request.form["event_date"])
        event.service_type = request.form["service_type"]
        event.venue = request.form.get("venue", "").strip()
        event.notes = request.form.get("notes", "").strip()
        db.session.commit()
        flash("Event updated.", "success")
        return redirect(url_for("event_detail", event_id=event.id))
    return render_template("event_form.html", event=event)


@app.route("/events/<int:event_id>/delete", methods=["POST"])
def event_delete(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash("Event deleted.", "info")
    return redirect(url_for("index"))


# ─────────────────────────────────────────────────────────────────────────────
# Set List
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/events/<int:event_id>/setlist/add", methods=["POST"])
def setlist_add(event_id):
    event = Event.query.get_or_404(event_id)
    song_id = int(request.form["song_id"])
    if not SetListItem.query.filter_by(event_id=event_id, song_id=song_id).first():
        max_pos = db.session.query(db.func.max(SetListItem.position)).filter_by(event_id=event_id).scalar() or 0
        item = SetListItem(
            event_id=event_id,
            song_id=song_id,
            position=max_pos + 1,
            notes=request.form.get("notes", "").strip(),
        )
        db.session.add(item)
        db.session.commit()
        flash("Song added to set list.", "success")
    else:
        flash("Song already in set list.", "warning")
    return redirect(url_for("event_detail", event_id=event_id))


@app.route("/events/<int:event_id>/setlist/<int:item_id>/remove", methods=["POST"])
def setlist_remove(event_id, item_id):
    item = SetListItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash("Song removed from set list.", "info")
    return redirect(url_for("event_detail", event_id=event_id))


@app.route("/events/<int:event_id>/setlist/reorder", methods=["POST"])
def setlist_reorder(event_id):
    """Receive a comma-separated list of item IDs in new order."""
    order = request.form.get("order", "")
    for pos, item_id in enumerate(order.split(","), start=1):
        if item_id.strip():
            item = SetListItem.query.get(int(item_id.strip()))
            if item and item.event_id == event_id:
                item.position = pos
    db.session.commit()
    return "", 204


# ─────────────────────────────────────────────────────────────────────────────
# Cast
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/events/<int:event_id>/cast/add", methods=["POST"])
def cast_add(event_id):
    event = Event.query.get_or_404(event_id)
    cast_member_id = int(request.form["cast_member_id"])
    if not EventCast.query.filter_by(event_id=event_id, cast_member_id=cast_member_id).first():
        ec = EventCast(
            event_id=event_id,
            cast_member_id=cast_member_id,
            role_override=request.form.get("role_override", "").strip() or None,
        )
        db.session.add(ec)
        db.session.commit()
        flash("Cast member added.", "success")
    else:
        flash("Already assigned.", "warning")
    return redirect(url_for("event_detail", event_id=event_id))


@app.route("/events/<int:event_id>/cast/<int:ec_id>/remove", methods=["POST"])
def cast_remove(event_id, ec_id):
    ec = EventCast.query.get_or_404(ec_id)
    db.session.delete(ec)
    db.session.commit()
    flash("Cast member removed.", "info")
    return redirect(url_for("event_detail", event_id=event_id))


@app.route("/events/<int:event_id>/cast/<int:ec_id>/sub", methods=["POST"])
def sub_set(event_id, ec_id):
    ec = EventCast.query.get_or_404(ec_id)
    if ec.sub:
        ec.sub.sub_name = request.form["sub_name"].strip()
        ec.sub.sub_contact = request.form.get("sub_contact", "").strip()
        ec.sub.confirmed = "confirmed" in request.form
        ec.sub.notes = request.form.get("notes", "").strip()
    else:
        sub = Sub(
            event_cast_id=ec_id,
            sub_name=request.form["sub_name"].strip(),
            sub_contact=request.form.get("sub_contact", "").strip(),
            confirmed="confirmed" in request.form,
            notes=request.form.get("notes", "").strip(),
        )
        db.session.add(sub)
    db.session.commit()
    flash("Sub updated.", "success")
    return redirect(url_for("event_detail", event_id=event_id))


@app.route("/events/<int:event_id>/cast/<int:ec_id>/sub/remove", methods=["POST"])
def sub_remove(event_id, ec_id):
    ec = EventCast.query.get_or_404(ec_id)
    if ec.sub:
        db.session.delete(ec.sub)
        db.session.commit()
        flash("Sub removed.", "info")
    return redirect(url_for("event_detail", event_id=event_id))


# ─────────────────────────────────────────────────────────────────────────────
# Rehearsals
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/events/<int:event_id>/rehearsals/add", methods=["POST"])
def rehearsal_add(event_id):
    event = Event.query.get_or_404(event_id)
    rehearsal = Rehearsal(
        event_id=event_id,
        rehearsal_date=date.fromisoformat(request.form["rehearsal_date"]),
        start_time=request.form.get("start_time", "").strip(),
        end_time=request.form.get("end_time", "").strip(),
        location=request.form.get("location", "").strip(),
        focus_notes=request.form.get("focus_notes", "").strip(),
        agenda=request.form.get("agenda", "").strip(),
    )
    db.session.add(rehearsal)
    db.session.commit()
    flash("Rehearsal added.", "success")
    return redirect(url_for("event_detail", event_id=event_id))


@app.route("/events/<int:event_id>/rehearsals/<int:r_id>/edit", methods=["POST"])
def rehearsal_edit(event_id, r_id):
    rehearsal = Rehearsal.query.get_or_404(r_id)
    rehearsal.rehearsal_date = date.fromisoformat(request.form["rehearsal_date"])
    rehearsal.start_time = request.form.get("start_time", "").strip()
    rehearsal.end_time = request.form.get("end_time", "").strip()
    rehearsal.location = request.form.get("location", "").strip()
    rehearsal.focus_notes = request.form.get("focus_notes", "").strip()
    rehearsal.agenda = request.form.get("agenda", "").strip()
    db.session.commit()
    flash("Rehearsal updated.", "success")
    return redirect(url_for("event_detail", event_id=event_id))


@app.route("/events/<int:event_id>/rehearsals/<int:r_id>/delete", methods=["POST"])
def rehearsal_delete(event_id, r_id):
    rehearsal = Rehearsal.query.get_or_404(r_id)
    db.session.delete(rehearsal)
    db.session.commit()
    flash("Rehearsal deleted.", "info")
    return redirect(url_for("event_detail", event_id=event_id))


# ─────────────────────────────────────────────────────────────────────────────
# Agenda (printable)
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/events/<int:event_id>/agenda")
def agenda(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template("agenda.html", event=event)


# ─────────────────────────────────────────────────────────────────────────────
# Song Library
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/songs")
def songs():
    all_songs = Song.query.order_by(Song.title).all()
    return render_template("songs.html", songs=all_songs)


@app.route("/songs/new", methods=["GET", "POST"])
def song_new():
    if request.method == "POST":
        song = Song(
            title=request.form["title"].strip(),
            artist=request.form.get("artist", "").strip(),
            key=request.form.get("key", "").strip(),
            notes=request.form.get("notes", "").strip(),
        )
        db.session.add(song)
        db.session.commit()
        flash("Song added to library.", "success")
        return redirect(url_for("songs"))
    return render_template("song_form.html", song=None)


@app.route("/songs/<int:song_id>/edit", methods=["GET", "POST"])
def song_edit(song_id):
    song = Song.query.get_or_404(song_id)
    if request.method == "POST":
        song.title = request.form["title"].strip()
        song.artist = request.form.get("artist", "").strip()
        song.key = request.form.get("key", "").strip()
        song.notes = request.form.get("notes", "").strip()
        db.session.commit()
        flash("Song updated.", "success")
        return redirect(url_for("songs"))
    return render_template("song_form.html", song=song)


@app.route("/songs/<int:song_id>/delete", methods=["POST"])
def song_delete(song_id):
    song = Song.query.get_or_404(song_id)
    db.session.delete(song)
    db.session.commit()
    flash("Song deleted.", "info")
    return redirect(url_for("songs"))


# ─────────────────────────────────────────────────────────────────────────────
# Cast Roster
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/roster")
def roster():
    members = CastMember.query.order_by(CastMember.name).all()
    return render_template("roster.html", members=members)


@app.route("/roster/new", methods=["GET", "POST"])
def roster_new():
    if request.method == "POST":
        member = CastMember(
            name=request.form["name"].strip(),
            role=request.form.get("role", "").strip(),
            email=request.form.get("email", "").strip(),
            phone=request.form.get("phone", "").strip(),
            notes=request.form.get("notes", "").strip(),
        )
        db.session.add(member)
        db.session.commit()
        flash("Cast member added to roster.", "success")
        return redirect(url_for("roster"))
    return render_template("cast_form.html", member=None)


@app.route("/roster/<int:member_id>/edit", methods=["GET", "POST"])
def roster_edit(member_id):
    member = CastMember.query.get_or_404(member_id)
    if request.method == "POST":
        member.name = request.form["name"].strip()
        member.role = request.form.get("role", "").strip()
        member.email = request.form.get("email", "").strip()
        member.phone = request.form.get("phone", "").strip()
        member.notes = request.form.get("notes", "").strip()
        db.session.commit()
        flash("Cast member updated.", "success")
        return redirect(url_for("roster"))
    return render_template("cast_form.html", member=member)


@app.route("/roster/<int:member_id>/delete", methods=["POST"])
def roster_delete(member_id):
    member = CastMember.query.get_or_404(member_id)
    db.session.delete(member)
    db.session.commit()
    flash("Cast member removed from roster.", "info")
    return redirect(url_for("roster"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
