"""全部の計算を順に（30 分以内）：最初の 10 分 → 2 日まで（5 つのシナリオを同時に）→ 90 日まで（ざっくり）→ 表と地図。

前もって python fetch_mesh.py data/mesh と python build_grid.py（データは data/、git に入れない）。
"""
import os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
FINE = ["base", "roam", "no_sdf", "slow_gov", "outdoor"]
ALL = FINE + ["close"]
env = dict(os.environ, PYTHONIOENCODING="utf-8")
t0 = time.time()


def step(msg):
    print(f"✅ {msg}（経過 {(time.time() - t0) / 60:.1f} 分）", flush=True)


subprocess.run([sys.executable, "micro.py"], cwd=HERE, env=env, check=True, stdout=open(os.path.join(HERE, "data", "micro_out.txt"), "w", encoding="utf-8"))
step("最初の 10 分")
procs = [subprocess.Popen([sys.executable, "macro.py", n], cwd=HERE, env=env,
                          stdout=open(os.path.join(HERE, "data", f"macro_{n}_out.txt"), "w", encoding="utf-8"), stderr=subprocess.STDOUT)
         for n in FINE]
for p in procs:
    if p.wait() != 0:
        sys.exit("macro.py が失敗（data/macro_*_out.txt）")
step("2 日まで（5 つのシナリオ）")
procs = [subprocess.Popen([sys.executable, "coarse.py", n], cwd=HERE, env=env,
                          stdout=open(os.path.join(HERE, "data", f"coarse_{n}_out.txt"), "w", encoding="utf-8"), stderr=subprocess.STDOUT)
         for n in ALL]
for p in procs:
    if p.wait() != 0:
        sys.exit("coarse.py が失敗（data/coarse_*_out.txt）")
step("90 日まで（ざっくり、6 つのシナリオ）")
subprocess.run([sys.executable, "report.py"] + ALL, cwd=HERE, env=env, check=True, stdout=subprocess.DEVNULL)
step("表と地図（results.md・maps/）")
