import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from googleapiclient.errors import HttpError
from pathlib import Path
import gcal
import logging
import pickle
import os
import random


DATE = datetime.now(timezone.utc)
SAVED_ROTATIONS_PATH = Path("rotations.pickle")


class Geo(Enum):
    AMERICAS = "🌎"
    EUROPE_AFRICA = "🌍"
    ASIA_AUSTRALIA = "🌏"


@dataclass
class Person:
    name: str
    nick: str
    geo: Geo
    lead: bool = False
    """<cal_override> at mozilla is used to send the calendar invitations"""
    cal_override: str = None

    def __repr__(self):
        return f"{self.name} [{self.nick}]"

    def get_cal_nick(self):
        return self.cal_override if self.cal_override else self.nick


@dataclass
class Rotation:
    leader: Person
    sheriffs: list

    def __repr__(self):
        return f"{self.leader}, {self.sheriffs}"


MEMBERS = [
    Person("Andrew Creskey", "acreskey", Geo.AMERICAS, True),
    Person("Bas Schouten", "bas", Geo.EUROPE_AFRICA, True, cal_override="bschouten"),
    Person("Benjamin De Kosnik", "bdekoz", Geo.AMERICAS, True),
    Person("Daniel Holbert", "dholbert", Geo.AMERICAS),
    Person("Dave Hunt", "davehunt", Geo.EUROPE_AFRICA),
    Person("Denis Palmeiro", "denispal", Geo.AMERICAS, True, cal_override="dpalmeiro"),
    Person("Doug Thayer", "dthayer", Geo.AMERICAS, True, cal_override="dothayer"),
    Person("Florian Quèze", "florian", Geo.EUROPE_AFRICA, True),
    Person(
        "Gregory Mierzwinski", "sparky", Geo.AMERICAS, True, cal_override="gmierzwinski"
    ),
    Person("Julien Wajsberg", "julienw", Geo.EUROPE_AFRICA, True),
    Person("Marc Leclair", "mleclair", Geo.AMERICAS),
    Person("Markus Stange", "mstange", Geo.AMERICAS, True),
    Person("Michael Comella", "mcomella", Geo.AMERICAS, True),
    Person("Mike Conley", "mconley", Geo.AMERICAS),
    Person("Nazim Can Altinova", "canova", Geo.EUROPE_AFRICA, cal_override="naltinova"),
    Person("Olli Pettay", "smaug", Geo.EUROPE_AFRICA),
    Person("Randell Jesup", "jesup", Geo.AMERICAS, cal_override="rjesup"),
    Person("Sean Feng", "sefeng", Geo.AMERICAS, True),
    Person("Frank Doty", "frankdoty", Geo.AMERICAS, cal_override="fdoty"),
    Person("Andrej Glavic", "andrej", Geo.AMERICAS, cal_override="aglavic"),
    Person(
        "Kimberly Sereduck", "kimberlythegeek", Geo.AMERICAS, cal_override="ksereduck"
    ),
    Person("Kash Shampur", "kshampur", Geo.AMERICAS),
]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--production",
        action="store_true",
        help=(
            "if set, performs all actions as if running in CI including "
            "adding calendar invites. This is not enabled by default to ease "
            "development, i.e. so we're not adding calendar invites every time"
        ),
    )
    return parser.parse_args()


def load_rotations():
    try:
        with SAVED_ROTATIONS_PATH.open(mode="rb") as html:
            rotations = pickle.load(html)
        if isinstance(rotations, list):
            # migrate to dict format with dates
            rotations_dict = {}
            for rotation in reversed(rotations):
                week = get_week(DATE - timedelta(weeks=len(rotations_dict) - 1))
                rotations_dict.setdefault(week, rotation)
            return rotations_dict
    except FileNotFoundError:
        rotations = {}
    return rotations


def generate_html(rotations):
    path = Path("docs")
    path.mkdir(exist_ok=True)
    fpath = (path / "index.html").with_suffix(".html")
    this_week = rotations[get_week(DATE)]
    next_week = rotations[get_week(DATE + timedelta(weeks=1))]
    with fpath.open(mode="w+") as html:
        html.write("<html><body><h1>Performance Triage</h1>")
        html.write(f"<p>Generated on {DATE}.</p>")
        html.write(f"<h2>This week</h2><ol>")
        html.write(f"<li><strong>{this_week.leader}</strong></li>")
        for s in this_week.sheriffs:
            html.write(f"<li>{s}</li>")
        html.write(f"</ol><h2>Next week</h2><ol>")
        html.write(f"<li><strong>{next_week.leader}</strong></li>")
        for s in next_week.sheriffs:
            html.write(f"<li>{s}</li>")
        html.write(f"</ol><h2>History</h2><ul>")
        for _, r in list(sorted(rotations.items(), reverse=True))[2:]:
            html.write(f"<li><strong>{r.leader}</strong>, {r.sheriffs}</li>")
        html.write("</ul></body></html>")


def generate_rotation(leaders, rotations):
    leader_candidates = leaders.copy()
    # remove recent leaders from pool
    for _, r in list(sorted(rotations.items()))[(len(leaders) - 1) * -1 :]:
        if r.leader in leader_candidates:
            leader_candidates.remove(r.leader)
    leader = random.choice(leader_candidates)

    sheriff_candidates = MEMBERS.copy()
    # remove leader from pool
    sheriff_candidates.remove(leader)
    # remove recent sheriffs from pool
    for w, r in list(sorted(rotations.items()))[-4:]:
        if r.leader in sheriff_candidates:
            sheriff_candidates.remove(r.leader)
        for sheriff in r.sheriffs:
            if sheriff in sheriff_candidates:
                sheriff_candidates.remove(sheriff)
    # pick sheriffs for each triage rotation
    sheriffs = []
    for _ in range(2):
        geos = {s.geo for s in [leader] + sheriffs}
        if len(geos) > 1:
            # remove sheriffs outside of selected geos from pool
            sheriff_candidates = [c for c in sheriff_candidates if c.geo in geos]
        if len(sheriff_candidates) > 0:
            random.shuffle(sheriff_candidates)
            sheriffs.append(sheriff_candidates.pop())
    return Rotation(leader, sheriffs)


def get_addresses_from_rotation(rotation):
    attendees = [rotation.leader] + [s for s in rotation.sheriffs]
    return [a.get_cal_nick() + "@mozilla.com" for a in attendees]


def add_gcal_reminder(is_production, rotation, generated_next_week):
    """Adds a triage reminder event to the Performance Team Google Calendar based on the rotation.
    See the top-of-file comment in gcal.py for requirements to run this function.

    This function may raise HttpError for google API or network failures and
    FileNotFoundError if the GCloud Project secrets are missing.
    """
    # TODO: the states (is_production, generated_next_week, & CI envvar) seem confusing - is there a cleaner solution?
    dry_run_mode = False
    if not generated_next_week:
        dry_run_mode = True
        print(
            (
                "INFO: for this script to be idempotent, we only add calendar reminders when we "
                "generate new rotations for next week. We did not generate it this time so we "
                "run add_gcal_reminder in dry run mode."
            )
        )

    if not is_production:
        dry_run_mode = True
        print(
            "INFO: --production was not specified so running add_gcal_reminder in dry run mode."
        )

    if not dry_run_mode:
        credentials = gcal.auth_as_user()
        service = gcal.get_calendar_service(credentials)

    # N.B.: for simplicity, this code assumes this script executes on Monday
    # or Tuesday the week before we want to set the reminder.
    #
    # Our reminders appear one week in advance. Note that we don't use the time fields.
    reminder_date = DATE + timedelta(weeks=1)
    # Show the reminder on Tuesday: we want the reminder to appear as early in
    # the week as possible but add a buffer day in case Monday is a holiday.
    while reminder_date.weekday() != 1:  # 1 == Tuesday
        reminder_date += timedelta(days=1)
    # To save time in changing the original implementation,
    # send_triage_reminder takes a yyyy-mm-dd instead of a datetime.
    reminder_date = reminder_date.strftime("%Y-%m-%d")

    addresses = get_addresses_from_rotation(rotation)

    if not dry_run_mode:
        gcal.send_triage_reminder(service, reminder_date, addresses)
    else:
        if os.getenv("CI"):
            # Don't print full email addresses to CI logs.
            addresses = [a.split("@")[0] for a in addresses]
        print(
            (
                "\nadd_gcal_reminder dry-run mode: would have created calendar "
                "invite with date {} and invitees {}"
            ).format(reminder_date, addresses)
        )


def add_gcal_reminder_manually(date):
    datetime.strptime(date, "%Y-%m-%d")  # Throws if date format is unexpected.

    rotations = load_rotations()
    this_week = rotations[get_week(DATE)]
    next_week = rotations[get_week(DATE + timedelta(weeks=1))]

    print(f"\nWhich rotation would you like to schedule for {date}?")
    print("\n(1) This week:")
    print(this_week)
    print("\n(2) Next week:")
    print(str(next_week) + "\n")

    selected_rotation = None
    while selected_rotation not in ["1", "2"]:
        print("Select rotation (1/2):")
        selected_rotation = input().strip()
    addresses = get_addresses_from_rotation(
        this_week if selected_rotation == "1" else next_week
    )

    credentials = gcal.auth_as_user()
    service = gcal.get_calendar_service(credentials)
    gcal.send_triage_reminder(service, date, addresses)


def get_week(date):
    week = datetime.fromisocalendar(*date.isocalendar()[:2], day=1)
    return week.strftime("%Y-%m-%d")


def main():
    args = parse_args()

    rotations = load_rotations()
    leaders = [m for m in MEMBERS if m.lead]
    while len(rotations) < len(leaders):
        # create some history to improve selection
        week = get_week(DATE - timedelta(weeks=(len(leaders) - len(rotations))))
        rotations.setdefault(week, generate_rotation(leaders, rotations))

    print(f"Generated on {DATE}")

    print("\nThis week:")
    this_week = get_week(DATE)
    if not rotations.get(this_week):
        rotations[this_week] = generate_rotation(leaders, rotations)
    print(f"{this_week}: {rotations[this_week]}")

    print("\nNext week:")
    next_week = get_week(DATE + timedelta(weeks=1))
    generated_next_week = False
    if not rotations.get(next_week):
        generated_next_week = True
        rotations[next_week] = generate_rotation(leaders, rotations)
    print(f"{next_week}: {rotations[next_week]}")

    print("\nHistory:")
    for week, rotation in list(sorted(rotations.items(), reverse=True))[2:]:
        print(f"{week}: {rotation}")

    generate_html(rotations)

    with SAVED_ROTATIONS_PATH.open(mode="wb") as f:
        pickle.dump(rotations, f)

    print("")  # Add a newline between rotation output and calendar reminder output.
    try:
        add_gcal_reminder(args.production, rotations[next_week], generated_next_week)
    except Exception as err:
        # If this script fails (returns a non-zero exit code), the triage rotation website will not
        # get updated. Since contacting the network to send a reminder can hit a lot of errors, we
        # catch all exceptions to be safe and avoid this possibility.
        # TODO: separate this into a separate build task to make generate rotation even safer.
        if type(err) is HttpError:
            logging.exception("during network request when adding google calendar reminder")
        elif type(err) is FileNotFoundError:
            logging.exception("unable to locate Google Cloud Project secrets when adding google calendar reminder")
        else:
            # Exception types include gcal.CredentialException & GoogleAuthError
            logging.exception('cause unknown')


if __name__ == "__main__":
    main()
