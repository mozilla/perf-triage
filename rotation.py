from dataclasses import dataclass
import random


@dataclass
class Person:
    name: str
    nick: str
    lead: bool = False


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
    Person("Kim Moir", "kmoir"),
    Person("Marc Leclair", "mleclair"),
    Person("Markus Stange", "mstange", True),
    Person("Michael Comella", "mcomella", True),
    Person("Mike Conley", "mconley"),
    Person("Nazim Can Altinova", "canova"),
    Person("Olli Pettay", "smaug"),
    Person("Randell Jesup", "jesup"),
    Person("Sean Feng", "sefeng", True),
]

leaders = [m for m in members if m.lead]
leaders = random.sample(leaders, len(leaders)) * 3
rotations = []

for index, leader in enumerate(leaders):
    candidates = members.copy()
    # remove leader from pool
    candidates.remove(leader)
    # remove recent sheriffs from pool
    for recent in rotations[-4:]:
        for sheriff in recent:
            if sheriff in candidates:
                candidates.remove(sheriff)
    # remove upcoming leaders from pool
    for sheriff in leaders[index + 1 : index + 5]:
        if sheriff in candidates:
            candidates.remove(sheriff)
    # pick sheriffs for each triage rotation
    sample = random.sample(candidates, 2)
    rotations.append([leader] + sample)

for rotation in rotations[:26]:
    print(", ".join([f"{s.name} [:{s.nick}]" for s in rotation]))
