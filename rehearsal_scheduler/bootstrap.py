#!/usr/bin/env python3
"""Bootstrap the scheduler from Google Calendar data."""
import os, sys
from datetime import date

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

from app import app, db
from models import Event, CastMember, EventCast, Sub, Rehearsal

with app.app_context():

    # ── Wipe existing data in FK-safe order ────────────────────────────
    from sqlalchemy import text
    db.session.execute(text("DELETE FROM subs"))
    db.session.execute(text("DELETE FROM event_cast"))
    db.session.execute(text("DELETE FROM set_list_items"))
    db.session.execute(text("DELETE FROM rehearsals"))
    db.session.execute(text("DELETE FROM events"))
    db.session.execute(text("DELETE FROM cast_members"))
    db.session.commit()

    # ── Cast Roster ────────────────────────────────────────────────────
    def cast(name, role, notes=""):
        m = CastMember(name=name, role=role, notes=notes)
        db.session.add(m); db.session.flush()
        return m

    # Big Crush cast
    sara       = cast("Sara",        "Vocalist",        "BC regular")
    charles    = cast("Charles",     "Vocalist",        "BC regular")
    joseph     = cast("Joseph",      "Vocalist",        "BC regular")
    aaron      = cast("Aaron",       "Vocalist",        "BC regular")
    michael    = cast("Michael",     "Vocalist",        "BC regular")
    katryna    = cast("Katryna",     "Vocalist",        "BC — sub for Sara")
    joe_evans  = cast("Joe Evans",   "Drums",           "BC session drummer")
    aaron_s    = cast("Aaron Smith", "Guitar",          "BC session guitarist")

    # Hip Service cast
    mel        = cast("Mel",         "Lead Vocalist",   "HS regular")
    dante      = cast("Dante",       "Vocalist",        "HS regular")
    alex_m     = cast("Alex M",      "Vocalist",        "HS regular")
    kenzie     = cast("Kenzie",      "Vocalist",        "HS regular; sub for Mel")
    rod        = cast("Rod",         "Keys",            "HS regular")
    luke       = cast("Luke",        "Vocalist",        "HS regular")
    paxton     = cast("Paxton",      "Vocalist",        "HS regular")
    kaleo      = cast("Kaleo",       "Vocalist",        "HS regular")
    robyn      = cast("Robyn",       "Lead Vocalist",   "HS primary")
    david      = cast("David",       "Guitar",          "HS regular")
    samee      = cast("Samee",       "Vocalist",        "HS — sub for Paxton/Luke")

    # ── Helper: create event ───────────────────────────────────────────
    def event(name, event_date, svc, venue="", notes=""):
        e = Event(name=name, event_date=event_date, service_type=svc,
                  venue=venue, notes=notes)
        db.session.add(e); db.session.flush()
        return e

    # ── Big Crush Gigs ─────────────────────────────────────────────────
    bc = [
        event("Big Crush 050926", date(2026,5,9),  "big_crush",
              "Villa Montalvo, 15400 Montalvo Rd, Saratoga CA",
              "Michelle Barsanti MOB (Jennifer + Phil) | 12pc (3 horns, perc)\n"
              "Ceremony sound · Cocktail sound/iPad · Dinner sound/iPad · Band sound/lights\n"
              "12:30p Sound/lights load in | 2:30 Band load in (done 3:30) | 5:30 Singers onsite | 7:00 Band START | 10:00 End\n"
              "Lauren Tyndall planner · MIO"),

        event("Big Crush 051626", date(2026,5,16), "big_crush",
              "Chateau St Jean, 85555 Sonoma Hwy, Kenwood CA",
              "Dino Minatta | HS2; 10pc\n"
              "Ceremony sound · Cocktail BATTERY system (iPad) · Band/dinner sound · Add (2) Gig Bars\n"
              "12:00 Sound/lights load in | 2:00 Band load in (done 3pm) | 3:00 Intimate vow (NO SOUND) | 3:30–4:30 Ceremony | 5:55 SAX plays w/ recording B&G entrance | 7:00–10:00 Band\n"
              "Aaron Smith guitar · Joe Evans drums"),

        event("Big Crush 052326", date(2026,5,23), "big_crush",
              "Family Farm, 1400 Portola Rd, Woodside CA",
              "Nik Malhotra | 11pc (3 horns) | Joe Evans drums\n"
              "Ceremony sound + pre-ceremony keys & trumpet (2 songs) · Cocktail TRIO (piano/bass/sax) · Dinner sound\n"
              "12:30 Sound/lights | 2:00 Band load in (done 3:15) | 4:00 Ceremony sound (keys+trumpet) | 5:00 Cocktail TRIO | 6:00 Dinner/Singers onsite | 7:30 Band | 10:30 End"),

        event("Big Crush 052926", date(2026,5,29), "big_crush",
              "The Estate Yountville, 6481 Washington St, Yountville CA",
              "Adam & Kelsey | 8pc (no horns)\n"
              "Ceremony sound/PIANO (LAWN) · Cocktail DUO piano+guitar (LAWN) · DJ backline/sound/lights in barrel room · ADD SAX??\n"
              "2:00 Sound/lights load in | 4:00 Band load in | 5–6 Ceremony sound; PIANO | 5:30 Singers | 6–7 Cocktail DUO | 7–10 Band (BRICK TERRACE PAVILLION)\n"
              "Kateryna for Sara"),

        event("Big Crush 061326", date(2026,6,13), "big_crush",
              "Tre Posti, 641 Main St, Saint Helena CA",
              "Holmes | 10pc | Jennifer Stone planner\n"
              "Ceremony sound · Piano+Guitar DUO ceremony\n"
              "1:00 Sound/lights load in | 2:30 Band load in | 3:30 Ceremony / Piano+Guitar DUO | 6:30 Singers onsite | 8:00 Band | 11:00 End\n"
              "Kat for Sara"),

        event("Big Crush 062126", date(2026,6,21), "big_crush",
              "Swabbies on the River, 5871 Garden Hwy, Sacramento CA",
              "Father's Day Show\n"
              "Drums load in 11:30am | Band load in 12:00 | Full band soundcheck w/ singers 1:00 | Band 2:00–6:00pm"),

        event("Big Crush 062626", date(2026,6,26), "big_crush",
              "Sun City Lincoln Hills, 965 Orchard Creek Ln, Lincoln CA",
              "Ticketed concert | 10pc\n"
              "7:30–9:30pm Show — (2) 45-min sets\n"
              "Load in/soundcheck TBD · Bring IEMs, mics"),

        event("Big Crush 071226", date(2026,7,12), "big_crush",
              "Belvedere Community Park, 450 San Rafael Ave, Belvedere Tiburon CA",
              "Belvedere Concert | 10pc · All production provided\n"
              "1:30p Band load in | 2:30 Full band soundcheck w/ singers | 3:30 Opener soundcheck | 4–4:15 Opener | 4:20–6:00 Band (no intermission)"),

        event("Big Crush 072526", date(2026,7,25), "big_crush",
              "1047 Lakeshore Blvd, Incline Village NV",
              "Private Party | 10pc (sax, trumpet) + dancers\n"
              "3:00 Sound/lights load in | 4:00 Band load in | 6:00 Singers/dancers onsite | 8:15–11:45 Band"),

        event("Big Crush 080126", date(2026,8,1),  "big_crush",
              "Menlo Country Club, 2300 Woodside Rd, Woodside CA",
              "Wedding | 10pc\n"
              "Ceremony sound · Cocktail sound (iPad)\n"
              "2:00 Sound/lights load in | 3:30 Band load in | 5:00 Ceremony | 5:30 Singers onsite | 6:00 Cocktails | 7–10 Band"),

        event("Big Crush 080826", date(2026,8,8),  "big_crush",
              "Wolf Family Vineyards, 2125 Inglewood Ave, Saint Helena CA",
              "Wedding | 10pc · Ceremony sound\n"
              "2:00 Sound/lights load in | 3:30 Band load in | 4:30 Ceremony | 6:30 Singers onsite | 8–11 Band"),

        event("Big Crush 081526", date(2026,8,15), "big_crush",
              "The Chateau at Incline Village, 955 Fairway Blvd, Incline Village NV",
              "Wedding | 10pc · Cocktail & dinner sound\n"
              "1:30p Sound/lights load in | 2:30 Band load in | 3:30–7:00 Cocktail & Dinner sound | 5:30 Singers onsite | 7:00–10:00 Band"),

        event("Big Crush 082226", date(2026,8,22), "big_crush",
              "Micke Grove Regional Park, 11793 N Micke Grove Rd, Lodi CA",
              "Celebration/Fundraiser | 10pc (corporate) · Sound & lighting provided\n"
              "3:00 Band load in | 4:00 Full band soundcheck | 5:00 Setup complete | 8–10pm Band"),

        event("Big Crush 082926", date(2026,8,29), "big_crush",
              "Inn at Spanish Bay, 2700 17 Mile Dr, Pebble Beach CA",
              "Wedding | 10pc · FORMAL WHITE SUITS · PAX 250\n"
              "1:30p Sound/lights load in | 7:00–7:20 Sax greets guests into ballroom | 7:20 Welcome/toast | 7:45–8:20 Band dinner set | 8:20–8:45 Toasts/special dances | 8:45–10:30 Band dance sets | 10:30 Discrete strike | 10:30–12:45 DJ afterparty"),

        event("Big Crush 083026", date(2026,8,30), "big_crush",
              "Swabbies on the River, 5871 Garden Hwy, Sacramento CA",
              "Drums load in 12:30p | Band load in 1:00 | Full band soundcheck w/ singers 2:00 | Band 3:00–7:00pm"),
    ]

    # ── Hip Service Gigs ───────────────────────────────────────────────
    hs = [
        event("Hip Service 042526", date(2026,4,25), "hip_service",
              "Cavallo Point",
              "Meyjes — Camille Jacinto Hale | HS1; 9pc · Ceremony sound · Cocktail sound\n"
              "7:45–11pm NO BREAKS\n"
              "Melanie confirmed · Rod & Kenzie as backup"),

        event("Hip Service 050826", date(2026,5,8),  "hip_service",
              "Ritz-Carlton Half Moon Bay",
              "Breakthrough T1D | HS1\n"
              "Robyn (no Mel)"),

        event("Hip Service 050926B", date(2026,5,9),  "hip_service",
              "OVE",
              "Caroline Tague & Ryan | HS1; 10pc · Ceremony sound · Cocktail sound · Dinner sound\n"
              "Robyn"),

        event("Hip Service 051626B", date(2026,5,16), "hip_service",
              "Viansa Winery, Sonoma",
              "Jamie Friedman | 11pc (3 horns) · 8–11pm approx\n"
              "Ceremony audio · Cocktail audio/iPad\n"
              "Robyn · Kathryn Kalabokes planner"),

        event("Hip Service 051726", date(2026,5,17), "hip_service",
              "Swabbies on the River",
              "HS1 Swabbies | Robyn"),

        event("Hip Service 052326B", date(2026,5,23), "hip_service",
              "",
              "Luke wedding Yuba | 8pc w/ sax\n"
              "Robyn · Kaleo · Paxton"),

        event("Hip Service 052426", date(2026,5,24), "hip_service",
              "Ranch at Lake Sonoma",
              "Jake + Amy | HS1; 10pc · Ceremony sound · Cocktail trio\n"
              "*Need coverage for LUKE — Samee confirmed"),

        event("Hip Service 053026", date(2026,5,30), "hip_service",
              "Mission Ranch",
              "Shannon Richards (bride) | HS1; 9pc (sax) · Andrina Lopes planner\n"
              "Ceremony sound/VIOLIN (Razz) · Cocktail DUO piano/sax (Jubel style) · Dinner sound iPad\n"
              "David guitar · Robyn"),

        event("Hip Service 061226", date(2026,6,12), "hip_service",
              "Brentwood",
              "HS Brentwood Concert\n"
              "Samee sub for Paxton"),

        event("Hip Service 061326B", date(2026,6,13), "hip_service",
              "Beaulieu Garden",
              "Erin Donoghue | HS1; 10pc | Vigil planner\n"
              "Duo for dinner (piano + sax or bass) · Check sound guidelines\n"
              "Paxton OUT — Kenzie sub\n"
              "Robyn · Kaleo · Luke · Kenzie"),

        event("Hip Service 062026", date(2026,6,20), "hip_service",
              "MPCC",
              "Liz Horton | 10pc · Dinner extra 3 speakers\n"
              "Rod keys · Robyn"),

        event("Hip Service 062726", date(2026,6,27), "hip_service",
              "Healdsburg",
              "Honts | HS1; 9pc · Ceremony sound/piano · Cocktail TRIO · BATTERY ceremony sound needed\n"
              "Robyn"),

        event("Hip Service 070326", date(2026,7,3),  "hip_service",
              "El Dorado Hills",
              "EDH | 4 dancers\n"
              "Robyn (hold)"),

        event("Hip Service 071126", date(2026,7,11), "hip_service",
              "",
              "Edson CVR | HS1; 10pc | Andrina Lopes planner\n"
              "Cocktail TRIO · Afterparty DJ Louie · 12 uplights for band room\n"
              "Rod keys · Melanie"),

        event("Hip Service 072526B", date(2026,7,25), "hip_service",
              "Stanly Ranch",
              "Stanly Ranch | HS1; 12pc · Ceremony sound · Strings\n"
              "Jennifer Solorzano planner · Erin Taylor · Robyn"),
    ]

    # ── Known sub assignments ──────────────────────────────────────────
    def add_cast_with_sub(ev, member, sub_member=None, sub_name=None,
                          sub_contact="", confirmed=True, notes=""):
        ec = EventCast(event_id=ev.id, cast_member_id=member.id)
        db.session.add(ec); db.session.flush()
        if sub_name or sub_member:
            name = sub_member.name if sub_member else sub_name
            s = Sub(event_cast_id=ec.id, sub_name=name,
                    sub_contact=sub_contact, confirmed=confirmed, notes=notes)
            db.session.add(s)
        return ec

    # BC 5/16 — Katryna for Sara; Aaron Smith & Joe Evans as session players
    bc_0516 = next(e for e in bc if e.name == "Big Crush 051626")
    add_cast_with_sub(bc_0516, sara, sub_member=katryna, confirmed=True)
    add_cast_with_sub(bc_0516, aaron_s)   # session guitar
    add_cast_with_sub(bc_0516, joe_evans) # session drums

    # BC 5/29 — Katryna for Sara
    bc_0529 = next(e for e in bc if e.name == "Big Crush 052926")
    add_cast_with_sub(bc_0529, sara, sub_member=katryna, confirmed=True)

    # BC 6/13 — Katryna for Sara
    bc_0613 = next(e for e in bc if e.name == "Big Crush 061326")
    add_cast_with_sub(bc_0613, sara, sub_member=katryna, confirmed=True)

    # BC 5/23 — Joe Evans drums
    bc_0523 = next(e for e in bc if e.name == "Big Crush 052326")
    add_cast_with_sub(bc_0523, joe_evans)

    # HS 4/25 — Mel confirmed; Alex M OUT (no sub yet); Rod & Kenzie backup
    hs_0425 = next(e for e in hs if e.name == "Hip Service 042526")
    add_cast_with_sub(hs_0425, mel,    confirmed=True)
    add_cast_with_sub(hs_0425, dante,  confirmed=True)
    add_cast_with_sub(hs_0425, alex_m, sub_name="TBD", confirmed=False, notes="Alex M OUT")
    add_cast_with_sub(hs_0425, rod)
    add_cast_with_sub(hs_0425, kenzie, notes="Backup for Mel")

    # HS 5/24 — Samee sub for Luke
    hs_0524 = next(e for e in hs if e.name == "Hip Service 052426")
    add_cast_with_sub(hs_0524, luke, sub_member=samee, confirmed=True)

    # HS 6/12 — Samee sub for Paxton
    hs_0612 = next(e for e in hs if e.name == "Hip Service 061226")
    add_cast_with_sub(hs_0612, paxton, sub_member=samee, confirmed=True)

    # HS 6/13 — Paxton OUT / Kenzie sub; known cast
    hs_0613 = next(e for e in hs if e.name == "Hip Service 061326B")
    add_cast_with_sub(hs_0613, robyn)
    add_cast_with_sub(hs_0613, kaleo)
    add_cast_with_sub(hs_0613, luke)
    add_cast_with_sub(hs_0613, paxton, sub_member=kenzie, confirmed=True)

    # HS 7/11 — Rod keys, Mel vocalist
    hs_0711 = next(e for e in hs if e.name == "Hip Service 071126")
    add_cast_with_sub(hs_0711, rod)
    add_cast_with_sub(hs_0711, mel)

    # ── Rehearsals → nearest upcoming event ───────────────────────────
    bc_rehearsal_data = [
        (date(2026,4,13), "Sara OUT"),
        (date(2026,4,20), "Charles OUT · Joseph confirmed"),
        (date(2026,4,27), "Charles OUT · Katryna confirmed"),
        (date(2026,5,4),  "Sara OUT · Michael confirmed · Katryna confirmed"),
        (date(2026,5,11), "Joseph confirmed · Aaron confirmed · Katryna confirmed"),
        (date(2026,5,18), ""),
        (date(2026,6,1),  "Sara OUT"),
        (date(2026,6,8),  ""),
        (date(2026,6,15), ""),
        (date(2026,6,22), ""),
        (date(2026,6,29), ""),
        (date(2026,7,6),  "Sara OUT"),
        (date(2026,7,13), ""),
        (date(2026,7,20), ""),
        (date(2026,7,27), ""),
        (date(2026,8,3),  "Sara OUT"),
        (date(2026,8,10), ""),
        (date(2026,8,17), ""),
        (date(2026,8,24), ""),
        (date(2026,8,31), ""),
    ]

    hs_rehearsal_data = [
        (date(2026,4,15), 'Mel confirmed for 4/25 · Dante confirmed · Alex M OUT'),
        (date(2026,4,22), 'Kenzie confirmed · Mel OUT · Rod confirmed · Dante confirmed'),
        (date(2026,4,29), '"Meet Virginia" by Train — 1st dance recording (Luke)'),
        (date(2026,5,6),  "Record 5/30 first dance Train song"),
        (date(2026,5,13), ""),
        (date(2026,5,20), ""),
        (date(2026,5,27), ""),
        (date(2026,6,3),  ""),
        (date(2026,6,10), ""),
        (date(2026,6,17), ""),
        (date(2026,6,24), ""),
        (date(2026,7,1),  ""),
        (date(2026,7,8),  ""),
        (date(2026,7,15), ""),
        (date(2026,7,22), ""),
    ]

    def assign_rehearsals(reh_data, sorted_events, start_time, end_time):
        for reh_date, focus in reh_data:
            # Nearest upcoming event after rehearsal date
            target = next((e for e in sorted_events if e.event_date > reh_date), sorted_events[-1])
            r = Rehearsal(event_id=target.id, rehearsal_date=reh_date,
                          start_time=start_time, end_time=end_time,
                          focus_notes=focus)
            db.session.add(r)

    bc_sorted = sorted(bc, key=lambda e: e.event_date)
    hs_sorted = sorted(hs, key=lambda e: e.event_date)

    assign_rehearsals(bc_rehearsal_data, bc_sorted, "7:00 PM", "10:00 PM")
    assign_rehearsals(hs_rehearsal_data, hs_sorted, "7:00 PM", "10:00 PM")

    db.session.commit()

    print(f"✓ {len(bc)} Big Crush events")
    print(f"✓ {len(hs)} Hip Service events")
    print(f"✓ {len(bc_rehearsal_data)} BC rehearsals assigned")
    print(f"✓ {len(hs_rehearsal_data)} HS rehearsals assigned")
    print(f"✓ {CastMember.query.count()} cast members")
    print(f"✓ {Sub.query.count()} known subs loaded")
    print("Done — open http://localhost:5000")
