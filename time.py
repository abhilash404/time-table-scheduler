from ortools.sat.python import cp_model


# INPUT DATA

batches = ["CSE_5_A", "CSE_5_D", "CST_5_A"]

subjects = {

    # ---------- CORE / MANDATORY THEORY ----------

    "CN": {"type": "theory", "weekly_slots": 3, "code": "PC_CN"},
    "FLAT": {"type": "theory", "weekly_slots": 3, "code": "PC_FLAT"},
    "ML": {"type": "theory", "weekly_slots": 3, "code": "PC_ML"},
    "UHVPE": {"type": "theory", "weekly_slots": 2, "code": "MC_UHV"},

    # ---------- PROFESSIONAL ELECTIVES (PARALLEL) ----------

    "SI": {"type": "theory", "weekly_slots": 3, "code": "PE"},
    "MC": {"type": "theory", "weekly_slots": 3, "code": "PE"},
    "RTS": {"type": "theory", "weekly_slots": 3, "code": "PE"},
    "DM_DW": {"type": "theory", "weekly_slots": 3, "code": "PE"},

    # ---------- LABS ----------

    "CN_LAB": {"type": "lab", "weekly_slots": 1, "code": "LAB_CN"},
    "IWT_LAB": {"type": "lab", "weekly_slots": 2, "code": "LAB_IWT"},
    "SSIPS_LAB": {"type": "lab", "weekly_slots": 2, "code": "LAB_SS"},
    "SKILL_PROJECT": {"type": "lab", "weekly_slots": 2, "code": "LAB_PJ"},

    # ---------- LUNCH ----------

    "LUNCH": {"type": "break", "weekly_slots": 5, "code": "LUNCH"}
}

batch_subjects = {
    "CSE_5_A": list(subjects.keys()),
    "CSE_5_D": list(subjects.keys()),
    "CST_5_A": list(subjects.keys())
}

faculty = {

    # ---------- CORE THEORY ----------

    "MR_SARTHAK_PADHI": ["CN"],
    "MRS_RASHMITA_MOHANTY": ["FLAT"],
    "DR_SUBHRA_SWETANISHA": ["FLAT"],
    "MR_NIHAR_RANJAN_NAYAK": ["FLAT"],

    "DR_REKHA_SAHU": ["ML","SKILL_PROJECT"],
    "DR_RAJESH_KUMAR_OJHA": ["ML"],

    "MS_KALPANA_MOHANTY": ["UHVPE"],
    "MR_ARUNI_NAYAK": ["UHVPE"],

    # ---------- ELECTIVES ----------

    "MS_SUSMITA_BISWAL": ["SI"],
    "DR_SAROJ_KANTA_MISRA": ["SI"],

    "MS_SHARMISTHA_PUHAN": ["MC"],
    "MR_ANIL_KUMAR_MEHER": ["MC"],

    "DR_BIKRAM_KESHARI_MISHRA": ["RTS"],
    "MR_ASIT_KUMAR_DAS": ["RTS"],

    "DR_PULAK_SAHOO": ["DM_DW"],
    "MS_ARKASHREE_PRIYADARSINI_MISHRA": ["DM_DW"],

    # ---------- LABS ----------

    "DR_RAJESH_KUMAR_OJHA_LAB": ["CN_LAB"],
    "MR_SAMBIT_KUMAR_MOHANTY": ["CN_LAB"],
    "MR_JITEN_KUMAR_MOHANTY": ["CN_LAB"],
    "MR_AMARJEET_MOHANTY": ["CN_LAB"],

    "MR_RABINARAYAN_MOHANTY": ["IWT_LAB"],
    "MR_SATYABRATA_JENA": ["IWT_LAB"],
    "DR_CHITTARANJAN_MOHAPATRA": ["IWT_LAB"],
    "MR_PRATAP_CHANDRA_PANIGRAHI": ["IWT_LAB"],

    "DUMMY_SSIPS": ["SSIPS_LAB"],

    "MRS_INDUPRAVA_MALLICK": ["SKILL_PROJECT"],
    "MR_PRABHUPAD_SAHOO": ["SKILL_PROJECT"],

    # ---------- LUNCH ----------

    "LUNCH_CSE_5_A": ["LUNCH"],
    "LUNCH_CSE_5_D": ["LUNCH"],
    "LUNCH_CST_5_A": ["LUNCH"]
}

rooms = {
    "658": {"type": "theory"},
    "659": {"type": "theory"},
    "655": {"type": "theory"},
    "656": {"type": "theory"},
    "657": {"type": "theory"},
    "336": {"type": "lab"},
    "315": {"type": "lab"},
    "340": {"type": "lab"},
    "LUNCH": {"type": "break"}
}

slots_per_day = 8
days = 5
time_slots = list(range(slots_per_day * days))
lunch_slot_offsets = [3, 4, 5, 6]


# MODEL

model = cp_model.CpModel()

X = {}   # (batch, subject, faculty, room, time)
E = {}   # (batch, elective_code, time)


# DECISION VARIABLES

for b in batches:
    for s in batch_subjects[b]:
        for f, teaches in faculty.items():
            if s not in teaches:
                continue

            if s == "LUNCH" and not f.endswith(b):
                continue

            for r, rdata in rooms.items():
                if rdata["type"] != subjects[s]["type"]:
                    continue

                for t in time_slots:
                    X[(b, s, f, r, t)] = model.NewBoolVar(
                        f"X_{b}_{s}_{f}_{r}_{t}"
                    )

# Elective code presence
for b in batches:
    for s in batch_subjects[b]:
        code = subjects[s]["code"]
        if code == "PE":
            for t in time_slots:
                E[(b, code, t)] = model.NewBoolVar(f"E_{b}_{code}_{t}")


# CONSTRAINTS

# 1. Weekly slots per subject
for b in batches:
    for s in batch_subjects[b]:
        model.Add(
            sum(
                X[(bb, ss, f, r, t)]
                for (bb, ss, f, r, t) in X
                if bb == b and ss == s
            ) == subjects[s]["weekly_slots"]
        )

# 2. Faculty clash
for f in faculty:
    for t in time_slots:
        model.Add(
            sum(
                X[(b, s, ff, r, tt)]
                for (b, s, ff, r, tt) in X
                if ff == f and tt == t
            ) <= 1
        )

# 3. Batch clash (non-parallel subjects)
for b in batches:
    for t in time_slots:
        model.Add(
            sum(
                X[(bb, s, f, r, tt)]
                for (bb, s, f, r, tt) in X
                if bb == b and tt == t and subjects[s]["code"] != "PE"
            ) <= 1
        )

# 4. Parallel electives (same code run together)
for (b, s, f, r, t), var in X.items():
    if subjects[s]["code"] == "PE":
        model.Add(var <= E[(b, "PE", t)])

for b in batches:
    for t in time_slots:
        model.Add(E[(b, "PE", t)] <= 1)

# 5. Lunch only in allowed slots
for (b, s, f, r, t), var in X.items():
    if s == "LUNCH" and (t % slots_per_day) not in lunch_slot_offsets:
        model.Add(var == 0)

# 6. Exactly one lunch per day per batch
for b in batches:
    for d in range(days):
        day_slots = [d * slots_per_day + o for o in lunch_slot_offsets]
        model.Add(
            sum(
                X[(bb, s, f, r, t)]
                for (bb, s, f, r, t) in X
                if bb == b and s == "LUNCH" and t in day_slots
            ) == 1
        )


# SOLVE

solver = cp_model.CpSolver()
status = solver.Solve(model)

print("Solver status:", solver.StatusName(status))

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print("\n--- TIMETABLE ---")
    for (b, s, f, r, t), var in X.items():
        if solver.Value(var):
            day = t // slots_per_day
            slot = t % slots_per_day
            print(f"{b} | Day {day} Slot {slot} | {s} | {f} | {r}")
