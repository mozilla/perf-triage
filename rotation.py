from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import pickle
import random


@dataclass
class Person:
    name: str
    nick: str
    lead: bool = False

    def __repr__(self):
        return f"{self.name} [{self.nick}]"


@dataclass
class Rotation:
    leader: Person
    sheriffs: list

    def __repr__(self):
        return f"{self.leader}, {self.sheriffs}"


members = [
    Person("Andrew Creskey", "acreskey", True),
    Person("Bas Schouten", "bas", True),
    Person("Benjamin De Kosnik", "bdekoz", True),
    Person("Daniel Holbert", "dholbert"),
    Person("Dave Hunt", "davehunt"),
    Person("Denis Palmeiro", "denispal", True),
    Person("Doug Thayer", "dthayer", True),
    Person("Florian Quèze", "florian"),
    Person("Gerald Squelart", "gerald", True),
    Person("Gregory Mierzwinski", "sparky", True),
    Person("Julien Wajsberg", "julienw", True),
    Person("Marc Leclair", "mleclair"),
    Person("Markus Stange", "mstange", True),
    Person("Michael Comella", "mcomella", True),
    Person("Mike Conley", "mconley"),
    Person("Nazim Can Altinova", "canova"),
    Person("Olli Pettay", "smaug"),
    Person("Randell Jesup", "jesup"),
    Person("Sean Feng", "sefeng", True),
]

DATE = datetime.now(timezone.utc)
STATE = Path("state/rotations.pickle")


def generate_html(rotations):
    path = Path("report")
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


try:
    with STATE.open(mode="rb") as html:
        rotations = pickle.load(html)
except FileNotFoundError:
    rotations = []


def generate_rotation():
    leader_candidates = leaders.copy()
    # remove recent leaders from pool
    for r in rotations[(len(leaders) - 1) * -1 :]:
        if r.leader in leader_candidates:
            leader_candidates.remove(r.leader)
    leader = random.choice(leader_candidates)

    sheriff_candidates = members.copy()
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
    sheriffs = random.sample(sheriff_candidates, 2)
    return Rotation(leader, sheriffs)


leaders = [m for m in members if m.lead]

while len(rotations) < len(leaders):
    # create some history to improve selection
    rotations.append(generate_rotation())

# generate new rotation
rotations.append(generate_rotation())

print(f"Generated on {DATE}\n")

print(f"This week: {rotations[-2]}")
print(f"Next week: {rotations[-1]}")

print("\nPrevious rotations:")
[print(r) for r in reversed(rotations[:-2])]

generate_html(rotations)

with STATE.open(mode="wb") as f:
    pickle.dump(rotations, f)
