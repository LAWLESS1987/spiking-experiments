"""Experiment 19: a tighter volley (pre-registered: prereg/PREREG_exp19_volley_jitter.md with its Amendments 1 and 2,
all committed before this file was first run on seeds 1-8).

CONTROL    exp16_rescore.run_once(s, "real"), imported unchanged: exp11's direct-inhibition network. The control's
           bar, ratio and selectivity are read from this run.
TREATMENT  run_arm(s, 0.0005): exp16_rescore.run_once's "real" path line for line, with ONE change to the dynamics:
           each burst spike's jitter is rng.normal(0, 0.0005), a 0.5 ms sd, in place of rng.normal(0, 0.002).
COUNTERS   run_arm also carries counters (lines marked COUNTER) that never feed back into the dynamics. The control's
           counters come from run_arm(s, 0.002), which must reproduce the imported control's spike counts and end
           weights exactly; the check is printed per seed (Amendment 2).
Seeds 1-8, 120 s. The regime guard, the bar (a AND b, exp11's lines), the keep rule, the mechanism reading, the drive
qualifier, the saturation note and the reproduction check are applied as the pre-registration states them and are
printed beside the numbers.
Run:  .venv\\Scripts\\python.exe exp19_volley_jitter.py > exp19_out.txt      Out: exp19_weights.npz
      .venv\\Scripts\\python.exe exp19_volley_jitter.py --smoke   (seed 0, 2 s: checks the code runs; reads nothing)
"""
import sys

import numpy as np
from brian2 import (network_operation, Hz, Network, NeuronGroup, PoissonGroup, SpikeGeneratorGroup, SpikeMonitor,
                    Synapses, ms, mV, prefs, second, seed as br_seed, start_scope)

import exp16_rescore as X                                  # the control, unchanged
from exp17_selectivity_new_seeds import sel                # exp17's measure, unchanged
from exp18_ltp_threshold import histogram, pass_ab, split  # exp11's scoring lines and exp18's report helpers

prefs.codegen.target = "numpy"
N, K = 100, 3
GROUPS = [range(0, 20), range(20, 40), range(40, 60)]
TRUE = [list(g) for g in GROUPS]
SEEDS = list(range(1, 9))
JITTER_CONTROL, JITTER_TREATMENT = 0.002, 0.0005           # fixed in the pre-registration, not tuned
GUARD_LOW, GUARD_HIGH, GUARD_SEEDS = 20, 534, 5            # regime guard
RESPONSE_S = 0.020                                         # Amendment 1: a response within 20 ms of the onset
SAT_W, SAT_SHARE = 1.8, 0.10                               # Amendment 1: 0.9 * wmax, and the 10% note
DRIVE_RISE = 1.20                                          # Amendment 1: "rises by more than 20%"
COUNTERS = ("n_pot10", "n_pot100", "n_dep10", "n_dep100", "dw_pot10", "dw_dep10")
PUBLISHED_REAL = {1: 1.83, 2: 1.56, 3: 1.92, 4: 1.86, 5: 1.9, 6: 1.91, 7: 1.9, 8: 1.83}   # exp16 real == exp11 direct


def run_arm(s, jitter, dur_s=120.0):
    """exp16_rescore.run_once(s, "real") line for line, with the burst jitter as a parameter. Lines marked COUNTER
    only record: nothing they write is read by the dynamics. (run_once's two null streams, shuf and desync, are not
    drawn from on the "real" path and are left out.)"""
    DUR = dur_s * second
    start_scope()
    br_seed(s)
    rng = np.random.default_rng(s)

    noise = PoissonGroup(N, rates=5 * Hz)
    times, idx = [], []
    onsets, centres, labels = [], [], []                   # COUNTER: each volley's first spike, centre and group
    for t in np.arange(0.05, float(DUR / second), 0.25):
        g = rng.integers(K)
        first = None
        for i in GROUPS[g]:
            ti = t + rng.normal(0, jitter)                 # CHANGED in the treatment: 0.0005 in place of 0.002
            times.append(ti); idx.append(int(i))
            first = ti if first is None else min(first, ti)
        onsets.append(first); centres.append(float(t)); labels.append(int(g))
    o = np.argsort(times)
    pattern = SpikeGeneratorGroup(N, np.array(idx)[o], np.array(times)[o] * second)

    out = NeuronGroup(K, """dv/dt = -v / (10*ms) : volt
                            dtheta/dt = -theta / (2000*ms) : volt""",
                      threshold="v > 5*mV + theta", reset="v = 0*mV; theta += 1*mV", method="exact")
    inhib = Synapses(out, out, on_pre="v_post = clip(v_post - 6*mV, -6*mV, 100*mV)")
    inhib.connect(condition="i != j")

    taupre = taupost = 20 * ms
    wmax, Apre = 2.0, 0.01
    Apost = -Apre * 1.05
    stdp = """w : 1
              dapre/dt = -apre / taupre : 1 (event-driven)
              dapost/dt = -apost / taupost : 1 (event-driven)
              n_pot10 : 1
              n_pot100 : 1
              n_dep10 : 1
              n_dep100 : 1
              dw_pot10 : 1
              dw_dep10 : 1
              tpre : second
              tpost : second"""                            # COUNTER: every line after the two traces
    on_pre = ("v_post += w * mV\napre += Apre\nw = clip(w + apost, 0, wmax)\n"
              "n_dep10 += int(t - tpost <= 10*ms)\n"         # COUNTER: depression with a post spike <= 10 ms before
              "n_dep100 += int(t - tpost <= 100*ms)\n"       # COUNTER
              "dw_dep10 += apost * int(t - tpost <= 10*ms)\n"  # COUNTER: its nominal amount (the trace)
              "tpre = t")                                    # COUNTER
    on_post = ("apost += Apost\nw = clip(w + apre, 0, wmax)\n"
               "n_pot10 += int(t - tpre <= 10*ms)\n"         # COUNTER: potentiation with a pre spike <= 10 ms before
               "n_pot100 += int(t - tpre <= 100*ms)\n"       # COUNTER
               "dw_pot10 += apre * int(t - tpre <= 10*ms)\n"   # COUNTER: its nominal amount (the trace)
               "tpost = t")                                  # COUNTER
    syns = []
    for src in (noise, pattern):
        syn = Synapses(src, out, stdp, on_pre=on_pre, on_post=on_post)
        syn.connect()
        syn.w = "rand() * 0.6"
        syn.tpre = -1 * second                             # COUNTER: no spike yet (a constant; draws nothing)
        syn.tpost = -1 * second                            # COUNTER
        syns.append(syn)
    n0, b0 = X.mats(syns)

    state = {"targets": None}

    @network_operation(dt=100 * ms)
    def normalise():
        tot = np.zeros(K)
        for syn in syns:
            np.add.at(tot, np.array(syn.j), np.array(syn.w))
        if state["targets"] is None:
            state["targets"] = tot.copy()
            return
        for syn in syns:
            j = np.array(syn.j)
            syn.w = np.array(syn.w) * (state["targets"][j] / np.maximum(tot[j], 1e-9))

    spk = SpikeMonitor(out)
    net = Network(noise, pattern, out, inhib, syns[0], syns[1], spk, normalise)
    net.run(DUR)
    n1, b1 = X.mats(syns)
    spikes = [int((np.array(spk.i) == k).sum()) for k in range(K)]
    burst = syns[1]                                        # COUNTER: read back, burst synapses only
    counts = {name: np.array(getattr(burst, name)) for name in COUNTERS}
    counts["i"], counts["j"] = np.array(burst.i), np.array(burst.j)
    sched = {"onset": np.array(onsets), "centre": np.array(centres), "group": np.array(labels)}
    out_spikes = (np.array(spk.i), np.array(spk.t / second))
    return n0, b0, n1, b1, spikes, counts, sched, out_spikes


def task(s, which):
    if which == "control":
        return X.run_once(s, "real")
    return run_arm(s, JITTER_CONTROL if which == "control_counted" else JITTER_TREATMENT)


def per_own_burst(counts, claim, sched):
    """Amendment 2: for each group, the counts on the synapses from its 20 inputs onto its own end-of-run claimer,
    summed over the three groups, divided by the number of those groups' bursts."""
    i, j = counts["i"], counts["j"]
    nb = sum(int((sched["group"] == g).sum()) for g in range(K))
    res = {}
    for name in COUNTERS:
        tot = 0.0
        for g in range(K):
            m = np.isin(i, TRUE[g]) & (j == claim[g])
            tot += float(counts[name][m].sum())
        res[name] = tot / nb
    return res


def responses(sched, out_spikes, claim):
    """Amendments 1 and 2: an output responds to a volley if it fires at least once within 20 ms after the volley's
    onset (its earliest input spike). Own = the volleys of the groups an output claims; other = the volleys of the
    groups it does not. Latency = the claimer's first spike in that window minus the onset (and, reported only,
    minus the volley's scheduled centre)."""
    oi, ot = out_spikes
    ts_k = [np.sort(ot[oi == k]) for k in range(K)]
    own_hit = own_n = oth_hit = oth_n = 0
    lat_on, lat_ce = [], []
    for onset, centre, g in zip(sched["onset"], sched["centre"], sched["group"]):
        for k in sorted(set(claim)):
            ts = ts_k[k]
            a = int(np.searchsorted(ts, onset, side="left"))
            fired = a < len(ts) and ts[a] <= onset + RESPONSE_S
            if claim[g] == k:
                own_n += 1; own_hit += int(fired)
                if fired:
                    lat_on.append(ts[a] - onset); lat_ce.append(ts[a] - centre)
            else:
                oth_n += 1; oth_hit += int(fired)
    return dict(own_hit=own_hit, own_n=own_n, oth_hit=oth_hit, oth_n=oth_n, lat_on=lat_on, lat_ce=lat_ce)


def saturation(b1, claim):
    w = np.concatenate([b1[claim[g], TRUE[g]] for g in range(K)])
    return int((w >= SAT_W).sum()), int(w.size)


def guard_hits(spikes, claim):
    why = []
    if min(spikes) < GUARD_LOW:
        why.append(f"an output under {GUARD_LOW} spikes")
    if max(spikes) > GUARD_HIGH:
        why.append(f"an output over {GUARD_HIGH} spikes")
    if len(set(claim)) == 1:
        why.append("one output claims all three groups")
    return why


def share(h, n):
    return f"{h}/{n} ({h / n:.3f})" if n else f"{h}/{n} (n/a)"


def ms_(vals, fn):
    return f"{1000 * fn(vals):.2f} ms" if len(vals) else "n/a"


def describe(arm, s, row, extra=""):
    print(f"{arm:9s} seed {s}: {'PASS' if row['ok'] else 'fail'} claim={row['claim']} per-group={row['per']} "
          f"ratio={row['ratio']}{extra} spk={row['spikes']} sel {row['sel0']:.2f}->{row['sel']:.2f} | "
          f"b {row['b']:.3f} n_g {row['ng']:.3f} s {row['s']:.3f} n {row['n']:.3f} o {row['o']:.3f}")
    c, r = row["per_burst"], row["resp"]
    print(f"          per own-group burst: dep10 {c['n_dep10']:.3f} dep100 {c['n_dep100']:.3f} pot10 {c['n_pot10']:.3f} "
          f"pot100 {c['n_pot100']:.3f} | nominal pot10 {c['dw_pot10']:+.5f} dep10 {c['dw_dep10']:+.5f} "
          f"net {c['dw_pot10'] + c['dw_dep10']:+.5f}")
    print(f"          responses within 20 ms: own {share(r['own_hit'], r['own_n'])}, other "
          f"{share(r['oth_hit'], r['oth_n'])}; latency from onset mean {ms_(r['lat_on'], np.mean)} median "
          f"{ms_(r['lat_on'], np.median)}; from centre mean {ms_(r['lat_ce'], np.mean)} | claimed burst synapses "
          f">= {SAT_W}: {row['sat'][0]}/{row['sat'][1]}")


def main():
    import os
    from multiprocessing import Pool
    if "--smoke" in sys.argv:
        X.DUR = 2 * second                                 # smoke only: shortens the imported control's run
        a = X.run_once(0, "real")
        b = run_arm(0, JITTER_CONTROL, dur_s=2.0)
        c = run_arm(0, JITTER_TREATMENT, dur_s=2.0)
        same = all(np.array_equal(x, y) for x, y in zip(a[:4], b[:4])) and a[4] == b[4]
        print("smoke: 2 s on seed 0; counted copy identical to the import:", same, "; spikes", a[4], b[4], c[4],
              "; counters read:", sorted(b[5]), "- no reading taken")
        return
    tasks = [(s, w) for s in SEEDS for w in ("control", "control_counted", "treatment")]
    nworkers = max(1, int(os.environ.get("EXP19_WORKERS", "8")))
    print("exp19: a tighter volley (burst jitter sd 0.5 ms against 2 ms) on exp11's direct inhibition, seeds %s "
          "(pre-registered: prereg/PREREG_exp19_volley_jitter.md with Amendments 1 and 2; %d workers, numpy)\n"
          % (SEEDS, nworkers))
    with Pool(nworkers) as pool:
        res = dict(zip(tasks, pool.starmap(task, tasks)))

    rows = {"control": [], "treatment": []}
    store = {}
    identical = {}
    for s in SEEDS:
        cn0, cb0, cn1, cb1, cspk = res[(s, "control")]
        kn0, kb0, kn1, kb1, kspk, kcounts, ksched, kout = res[(s, "control_counted")]
        identical[s] = (all(np.array_equal(x, y) for x, y in ((cn0, kn0), (cb0, kb0), (cn1, kn1), (cb1, kb1)))
                        and cspk == kspk)
        tn0, tb0, tn1, tb1, tspk, tcounts, tsched, tout = res[(s, "treatment")]
        for arm, (n0, b0, n1, b1, spikes), (counts, sched, outsp) in (
                ("control", (cn0, cb0, cn1, cb1, cspk), (kcounts, ksched, kout)),
                ("treatment", (tn0, tb0, tn1, tb1, tspk), (tcounts, tsched, tout))):
            ok, claim, per, ratio = pass_ab(n1 + b1)
            b, ng, sl, nn, oo = split(n1, b1, claim)
            row = dict(seed=s, ok=ok, claim=claim, per=per, ratio=ratio, spikes=spikes, sel0=sel(b0, TRUE),
                       sel=sel(b1, TRUE), b=b, ng=ng, s=sl, n=nn, o=oo, per_burst=per_own_burst(counts, claim, sched),
                       resp=responses(sched, outsp, claim), sat=saturation(b1, claim), guard=guard_hits(spikes, claim))
            rows[arm].append(row)
            for name, arr in (("n0", n0), ("b0", b0), ("n1", n1), ("b1", b1)):
                store[f"{arm}_s{s}_{name}"] = arr
            for name in COUNTERS:
                store[f"{arm}_s{s}_{name}"] = counts[name]
            store[f"{arm}_s{s}_out_i"], store[f"{arm}_s{s}_out_t"] = outsp
            store[f"{arm}_s{s}_onset"], store[f"{arm}_s{s}_group"] = sched["onset"], sched["group"]

    for arm in ("control", "treatment"):
        for row in rows[arm]:
            s = row["seed"]
            extra = ""
            if arm == "control":
                pub = PUBLISHED_REAL[s]
                extra = (f"  (exp16 published {pub}{'' if row['ratio'] == pub else ' MISMATCH'}; counted copy "
                         f"{'IDENTICAL' if identical[s] else 'DIFFERS'})")
            describe(arm, s, row, extra)
        print()

    ctl, trt = rows["control"], rows["treatment"]
    print("Per-seed distributions (bins of 0.1), read beside the counts:")
    for arm, rr in (("control", ctl), ("treatment", trt)):
        histogram(f"{arm} ratio", [r["ratio"] for r in rr])
        histogram(f"{arm} selectivity", [r["sel"] for r in rr])
    print()
    repro = sum(r["ratio"] == PUBLISHED_REAL[r["seed"]] for r in ctl)
    print(f"REPRODUCTION: control matches exp16's published ratio on {repro}/8 seeds")
    print(f"COPY CHECK: the counted control is identical to the imported control on {sum(identical.values())}/8 seeds")
    hit = [r for r in trt if r["guard"]]
    print(f"REGIME GUARD (treatment): {len(hit)}/8 seeds out of regime" +
          "".join(f"; seed {r['seed']}: {', '.join(r['guard'])}" for r in hit) +
          f"   (control, for reference: {sum(bool(r['guard']) for r in ctl)}/8)")
    if len(hit) >= GUARD_SEEDS:
        print("READING (pre-registered): the tighter volley moved the network OUT OF ITS REGIME. Stopped here: no "
              "reading on the mechanism, no rerun, no change.")
    else:
        cp, tp = sum(r["ok"] for r in ctl), sum(r["ok"] for r in trt)
        print(f"BAR (a AND b): control {cp}/8, treatment {tp}/8")
        kept = tp > cp
        print("KEEP RULE (pre-registered):", "KEPT -- strictly more seeds than the control" if kept else
              "NOT KEPT -- not strictly more seeds than the control (recorded as is)")
        cs, ts = sum(r["sel"] >= 2.0 for r in ctl), sum(r["sel"] >= 2.0 for r in trt)
        cm, tm = float(np.mean([r["sel"] for r in ctl])), float(np.mean([r["sel"] for r in trt]))
        lower = [s for s, c, t in zip(SEEDS, ctl, trt)
                 if identical[s] and t["per_burst"]["n_dep10"] < c["per_burst"]["n_dep10"]]
        c1, c2, c3 = tp >= 6, (ts >= cs and tm >= cm), len(lower) >= 6
        print(f"MECHANISM (1) (a AND b) on >= 6 of 8: treatment {tp}/8 -> {'holds' if c1 else 'fails'}")
        print(f"MECHANISM (2) selectivity >= 2.0 on control {cs}/8, treatment {ts}/8; mean control {cm:.3f}, "
              f"treatment {tm:.3f} -> {'holds' if c2 else 'fails'}")
        print(f"MECHANISM (3) depression events within 10 ms per own-group burst lower than the control's on "
              f"{len(lower)}/8 seeds {lower} -> {'holds' if c3 else 'fails'}")
        reading = "SUPPORTED" if (c1 and c2 and c3) else ("REFUTED" if (c3 and not c1) else "UNDETERMINED")
        meaning = {"SUPPORTED": "the volley's timing can lift the equilibrium past the bar",
                   "REFUTED": "the volley's timing moved and the equilibrium did not",
                   "UNDETERMINED": "reported as the numbers"}[reading]
        ch, cn = sum(r["resp"]["own_hit"] for r in ctl), sum(r["resp"]["own_n"] for r in ctl)
        th, tn = sum(r["resp"]["own_hit"] for r in trt), sum(r["resp"]["own_n"] for r in trt)
        rise = (th / tn) / (ch / cn) if cn and tn and ch else float("nan")
        print(f"DRIVE: own-group volleys answered within 20 ms, pooled: control {share(ch, cn)}, treatment "
              f"{share(th, tn)}; treatment/control {rise:.3f}")
        sc = [sum(r["sat"][0] for r in rr) / sum(r["sat"][1] for r in rr) for rr in (ctl, trt)]
        print(f"SATURATION: claimed burst synapses >= {SAT_W}, pooled: control {sc[0]:.3f}, treatment {sc[1]:.3f}")
        qual = []
        if reading == "SUPPORTED" and rise > DRIVE_RISE:
            qual.append("timing and drive together, not separated")
        if sc[1] > SAT_SHARE:
            qual.append("the ceiling, not timing, may be what moved")
        print(f"READING (pre-registered): {reading} -- {meaning}" + "".join(f"; NOTE: {q}" for q in qual))
    np.savez_compressed("exp19_weights.npz", **store)
    print("saved exp19_weights.npz")


if __name__ == "__main__":
    main()
