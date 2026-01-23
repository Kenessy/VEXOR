from pathlib import Path
path = Path('G:/AI/mirror/VRAXION/tournament_phase6.py')
lines = path.read_text().splitlines()

def dump(a,b):
    for i in range(a,b+1):
        if 1 <= i <= len(lines):
            print(f'{i:04d}: {lines[i-1]}')

print('--- core hyperparams ---')
dump(60,110)
print('--- scale/agc/warmup defs ---')
dump(150,210)
print('--- thermo/panic/cadence governor ---')
dump(300,460)
print('--- apply_update_agc ---')
dump(490,545)
print('--- inertia auto / dwell ---')
dump(548,585)
print('--- model init ptr params ---')
dump(630,670)
print('--- pointer update logic ---')
dump(1060,1165)
print('--- cadence auto adjust ---')
dump(1240,1265)
print('--- dwell stats ---')
dump(1316,1335)
print('--- training loop: walk pulse + sharding + agc + plateau + thermo + cadence ---')
dump(1980,2105)
print('--- logging ctrl line ---')
dump(2120,2185)
