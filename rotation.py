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
    Person("Justin Link", "jlink", Geo.AMERICAS),
    Person(
        "Emilio Cobos Álvarez", "emilio", Geo.EUROPE_AFRICA, cal_override="ealvarez"
    ),
    Person("Iain Ireland", "iain", Geo.AMERICAS, cal_override="iireland"),
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

    html = """
<html>

<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Performance Triage: Rotation</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0/dist/css/bootstrap.min.css" rel="stylesheet"
        integrity="sha384-gH2yIJqKdNHPEq0n4Mqa/HGKIhSkIHeL5AyhkYV8i59U5AR6csBvApHHNl/vI1Bx" crossorigin="anonymous">
</head>

<body>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0/dist/js/bootstrap.bundle.min.js"
        integrity="sha384-A3rJD856KowSb7dwlZdYEkO39Gagi7vIsF0jrRAoQmDKKtQBHUuLZ9AsSv4jD4Xa"
        crossorigin="anonymous"></script>

    <div class="container">
        <header class="d-flex flex-wrap justify-content-center py-3 mb-4 border-bottom">
            <a href="/" class="d-flex align-items-center mb-3 mb-md-0 me-md-auto text-dark text-decoration-none">
                <svg class="bi me-2" width="40" height="32">
                    <use xlink:href="#bootstrap"></use>
                </svg>
                <span class="fs-4">Performance Triage: Rotation</span>
            </a>

            <ul class="nav nav-pills">
                <li class="nav-item"><a href="calculator.html" class="nav-link">Impact Calculator</a></li>
                <li class="nav-item"><a href="#" class="nav-link active" aria-current="page">Rotation</a>
                </li>
            </ul>

            <a class="mx-3 d-flex" href="https://github.com/mozilla/perf-triage" target="_blank" rel="noopener noreferrer" title="Go to the Git repository (this opens in a new window)">
              <svg width="22" height="22" class="octicon octicon-mark-github m-auto" viewBox="0 0 16 16" version="1.1" aria-label="github"><path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path></svg>
            </a>
        </header>
    </div>

    <div class="container">

        <div class="row">

            <div class="col-sm-6">
                <div class="card mb-3">
                    <div class="card-header text-bg-primary">
                        This week
                    </div>
                    <ol class="list-group list-group-flush">
                        <li class="list-group-item"><strong>{{this_week.leader}}</strong></li>
                        {% for sheriff in this_week.sheriffs %}<li class="list-group-item">{{sheriff}}</li>
                        {% endfor %}
                    </ol>
                </div>
            </div>

            <div class="col-sm-6">
                <div class="card mb-3">
                    <div class="card-header text-bg-secondary">
                        Next week
                    </div>
                    <ol class="list-group list-group-flush">
                        <li class="list-group-item"><strong>{{next_week.leader}}</strong></li>
                        {% for sheriff in next_week.sheriffs %}<li class="list-group-item">{{sheriff}}</li>
                        {% endfor %}
                    </ol>
                </div>
            </div>

        </div>

        <div class="row">

            <div class="col">
                <div class="card mb-3">
                    <div class="card-header">
                        History
                    </div>
                    <ul class="list-group list-group-flush">
                        {% for date in history %}<li class="list-group-item">{{ date }}: <strong>{{ history[date].leader }}</strong>, {{ history[date].sheriffs }}</li>
                        {% endfor %}
                    </ul>
                </div>
            </div>
        </div>

        <div class="mb-3">Generated on {{timestamp}}.</div>

    </div>
</body>

</html>"""

    import jinja2
    environment = jinja2.Environment()
    template = environment.from_string(html)
    history = dict(sorted(rotations.items(), reverse=True)[2:])

    with fpath.open(mode="w+") as html:
        html.write(template.render(
            this_week=this_week,
            next_week=next_week,
            history=history,
            timestamp=DATE))


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
