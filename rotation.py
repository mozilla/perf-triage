from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
import pickle
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
    Person("Gerald Squelart", "gerald", Geo.ASIA_AUSTRALIA, True),
    Person("Gregory Mierzwinski", "sparky", Geo.AMERICAS, True, cal_override="gmierzwinski"),
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
]


def generate_html(rotations):
    path = Path("docs")
    path.mkdir(exist_ok=True)
    fpath = (path / "index.html").with_suffix(".html")
    with fpath.open(mode="w+") as html:
        html.write("<html><body><h1>Performance Triage</h1>")
        html.write(f"<p>Generated on {DATE}.</p>")
        html.write(f"<h2>This week</h2><ol>")
        html.write(f"<li><strong>{rotations[-2].leader}</strong></li>")
        for s in rotations[-2].sheriffs:
            html.write(f"<li>{s}</li>")
        html.write(f"</ol><h2>Next week</h2><ol>")
        html.write(f"<li><strong>{rotations[-1].leader}</strong></li>")
        for s in rotations[-1].sheriffs:
            html.write(f"<li>{s}</li>")
        html.write(f"</ol><h2>History</h2><ul>")
        for r in reversed(rotations[:-2]):
            html.write(f"<li><strong>{r.leader}</strong>, {r.sheriffs}</li>")
        html.write("</ul></body></html>")


def generate_rotation(leaders, rotations):
    leader_candidates = leaders.copy()
    # remove recent leaders from pool
    for r in rotations[(len(leaders) - 1) * -1 :]:
        if r.leader in leader_candidates:
            leader_candidates.remove(r.leader)
    leader = random.choice(leader_candidates)

    sheriff_candidates = MEMBERS.copy()
    # remove leader from pool
    sheriff_candidates.remove(leader)
    # remove recent sheriffs from pool
    for r in rotations[-4:]:
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


def main():
    try:
        with SAVED_ROTATIONS_PATH.open(mode="rb") as html:
            rotations = pickle.load(html)
    except FileNotFoundError:
        rotations = []

    leaders = [m for m in MEMBERS if m.lead]

    while len(rotations) < len(leaders):
        # create some history to improve selection
        rotations.append(generate_rotation(leaders, rotations))

    # generate new rotation
    rotations.append(generate_rotation(leaders, rotations))

    print(f"Generated on {DATE}\n")

    print(f"This week: {rotations[-2]}")
    print(f"Next week: {rotations[-1]}")

    print("\nPrevious rotations:")
    [print(r) for r in reversed(rotations[:-2])]

    generate_html(rotations)

    with SAVED_ROTATIONS_PATH.open(mode="wb") as f:
        pickle.dump(rotations, f)


if __name__ == '__main__':
    main()
