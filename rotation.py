from dataclasses import dataclass
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

ROTATIONS = 2
HISTORY = "rotations.pickle"

try:
    with open(HISTORY, "rb") as f:
        history = pickle.load(f)
except FileNotFoundError:
    history = []

rotations = []
leaders = [m for m in members if m.lead]
leader_candidates = leaders.copy()
# remove recent leaders from pool
for r in history[(len(leaders) - ROTATIONS) * -1 :]:
    if r.leader in leader_candidates:
        leader_candidates.remove(r.leader)

leader_candidates = random.sample(leader_candidates, ROTATIONS)

for index, leader in enumerate(leader_candidates):
    sheriff_candidates = members.copy()
    # remove leader from pool
    sheriff_candidates.remove(leader)
    # remove recent sheriffs from pool
    for r in history[-4:]:
        for sheriff in r.sheriffs:
            if sheriff in sheriff_candidates:
                sheriff_candidates.remove(sheriff)
    # remove upcoming leaders from pool
    for sheriff in leader_candidates[index + 1 : index + 5]:
        if sheriff in sheriff_candidates:
            sheriff_candidates.remove(sheriff)
    # pick sheriffs for each triage rotation
    sheriffs = random.sample(sheriff_candidates, 2)
    rotations.append(Rotation(leader, sheriffs))

print("\nNEW ROTATIONS:")
[print(r) for r in rotations]

print("\nRECENT ROTATIONS:")
[print(r) for r in reversed(history)]

history.extend(rotations)
with open(HISTORY, "wb") as f:
    pickle.dump(history[len(leaders) * -1 :], f)
