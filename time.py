batches = ["CST_3"]

subjects = {
    "NET": {
        "type": "theory",
        "weekly_slots": 2
    },
    "DBMS_LAB": {
        "type": "lab",
        "weekly_slots": 2
    }
}

faculty = {
    "Sarthak": ["NET"],
    "Anita": ["DBMS_LAB"]
}

rooms = {
    "R658": {"type": "theory", "capacity": 90},
    "LAB1": {"type": "lab", "capacity": 30}
}

time_slots = [0, 1, 2, 3]


from ortools.sat.python import cp_model

model = cp_model.CpModel()

X = {}

for b in batches:
    for s in subjects:
        for f in faculty:
            # Faculty must be able to teach subject
            if s not in faculty[f]:
                continue

            for r in rooms:
                # Room must match subject type
                if subjects[s]["type"] != rooms[r]["type"]:
                    continue

                for t in time_slots:
                    X[(b, s, f, r, t)] = model.NewBoolVar(
                        f"X_{b}_{s}_{f}_{r}_{t}"
                    )


for b in batches:
    for s in subjects:
        model.Add(
            sum(
                X[(b, s, f, r, t)]
                for (bb, ss, f, r, t) in X
                if bb == b and ss == s
            )
            == subjects[s]["weekly_slots"]
        )

for b in batches:
    for t in time_slots:
        model.Add(
            sum(
                X[(bb, s, f, r, tt)]
                for (bb, s, f, r, tt) in X
                if bb == b and tt == t
            )
            <= 1
        )

for f in faculty:
    for t in time_slots:
        model.Add(
            sum(
                X[(b, s, ff, r, tt)]
                for (b, s, ff, r, tt) in X
                if ff == f and tt == t
            )
            <= 1
        )

solver = cp_model.CpSolver()
status = solver.Solve(model)

if status == cp_model.OPTIMAL:
    for (b, s, f, r, t), var in X.items():
        if solver.Value(var) == 1:
            print(
                f"Batch {b} | Subject {s} | Faculty {f} | Room {r} | Slot {t}"
            )
