#!/usr/bin/env python3

import json
from pathlib import Path
import re
from subprocess import check_output

import project
import tracks

DIR = Path(__file__).resolve().parent
REPO = DIR.parent
IPC_DIR = REPO.parent
IMAGES_DIR = IPC_DIR / "images"
HAS_APPTAINER = not project.running_on_cluster()

class IPCPlanner:
    MAIN_LABELS = ["Name", "Description", "Authors", "License", "Tracks"]
    PDDL_PROPERTIES = ["DerivedPredicates",
                      "UniversallyQuantifiedPreconditions",
                      "ExistentiallyQuantifiedPreconditions",
                      "UniversallyQuantifiedEffects",
                      "NegativePreconditions",
                      "EqualityPreconditions",
                      "InequalityPreconditions",
                      "ConditionalEffects",
                      "ImplyPreconditions"]
    EMAIL_PATTERN = re.compile(r"(?P<name>[^<>]+)\<(?P<email>[A-z0-9.-]+@[A-z0-9.-]+\.\w+)\>")

    def __init__(self, image_path):
        self.image_path = Path(image_path)
        self.shortname = self.image_path.stem.replace(".", "_")
        assert self.image_path.exists(), self.image_path
        if HAS_APPTAINER:
            self._read_labels()

    def _read_labels(self):
        output = check_output(["apptainer", "inspect", "--labels", "--json", str(self.image_path)])
        properties = json.loads(output.decode()).get("data", {}).get("attributes", {}).get("labels", {})

        self.warnings = []
        for label in IPCPlanner.MAIN_LABELS + [f"Supports{p}" for p in IPCPlanner.PDDL_PROPERTIES]:
            if label not in properties:
                self.warnings.append(f"Missing label: {label}")

        self.name = properties.get("Name", "").strip()
        self.description = properties.get("Description", "").strip()

        self.authors = [a.strip() for a in properties.get("Authors", "").split(",")]
        self.author_names = []
        self.author_emails = []
        for author in self.authors:
            m = re.match(IPCPlanner.EMAIL_PATTERN, author)
            if m:
                self.author_names.append(m.group("name").strip())
                self.author_emails.append(m.group("email"))
            else:
                self.author_names.append(author)
                self.warnings.append(f"Author does not match pattern: '{author}'")

        self.license = properties.get("License", "")
        if self.license not in ["GPL 3", "MIT"]:
            self.warnings.append(f"Unknown license '{self.license}'")

        self.tracks = set([t.strip().lower() for t in properties.get("Tracks", "").split(",")])
        if not self.tracks:
            self.warnings.append(f"Planner does not participate in any tracks")
        for track in self.tracks:
            if track not in tracks.ALL:
                self.warnings.append(f"Unknown track '{track}'")

        self.unconditionally_supports = set()
        self.conditionally_supports = dict()
        for p in IPCPlanner.PDDL_PROPERTIES:
            label = f"Supports{p}"
            answer = properties.get(label, "no").strip().lower()
            if answer == "yes":
                self.unconditionally_supports.add(p)
            elif answer.startswith("partially"):
                self.conditionally_supports[p] = answer
            elif answer != "no":
                self.warnings.append(f"Answer to support question unclear '{label}: {answer}'")

SINGLE_CORE_LEARNERS = [
    "downward_smac.learn.sif",
    "pgp.learn.sif",
    "huzar.learn.sif",
    "ngpnum.learn.sif",
    "ngpstrips.learn.sif",
    "gofai.learn.sif",
    "asnets.learn.sif",
    "h_policy.learn.sif",
]

MULTI_CORE_LEARNERS = [
    "gofai.multicore.learn.sif",
    "muninn_10h.learn.sif",
    #"muninn.learn.sif",
]

SINGLE_CORE_PLANNERS = [
    "huzar.plan.sif",
    "ngpnum.plan.sif",
    "ngpstrips.plan.sif",
    "gofai.plan.sif",
    "asnets.plan.sif",
    "h_policy.plan.sif",
]

MULTI_CORE_PLANNERS = [
    "gofai.plan.sif",
    "muninn.plan.sif",
]


def get_learners(track=None):
    paths = SINGLE_CORE_LEARNERS if track == tracks.SINGLE_CORE else MULTI_CORE_LEARNERS
    return [IPCPlanner(IMAGES_DIR / path) for path in paths]


def get_all_learners():
    return get_learners(tracks.SINGLE_CORE) + get_learners(tracks.MULTI_CORE)


def get_participating(track=None):
    planners = []
    for image in IPC_DIR.glob("*/*.sif"):
        planner = IPCPlanner(image)
        if track is None or track in planner.tracks:
            planners.append(planner)
    return planners

def create_website_text(track=None):
    if track is None:
        return "\n".join(create_website_text(track) for track in tracks.ALL)

    lines = [f"### {track}"]
    for planner in get_participating(track):
        lines.append(f"""
* **{planner.name}** [(planner abstract)](TODO{planner.shortname}_{track}.pdf)
  *{", ".join(planner.author_names)}*
  {planner.description}""")
    return "\n".join(lines)

if __name__ == "__main__":
    print(create_website_text())
    print()
    for planner in get_participating():
        for w in planner.warnings:
            print(f"{planner.shortname}: {w}")
