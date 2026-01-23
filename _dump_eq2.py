from pathlib import Path
path = Path('G:/AI/mirror/VRAXION/tournament_phase6.py')
lines = path.read_text().splitlines()

def dump(a,b):
    for i in range(a,b+1):
        if 1 <= i <= len(lines):
            print(f'{i:04d}: {lines[i-1]}')

print('--- CadenceGovernor ---')
dump(360,450)
print('--- apply_update_agc ---')
dump(493,542)
print('--- dwell/inertia auto ---')
dump(548,580)
print('--- pointer update (inertia/deadzone/vel) ---')
dump(1066,1145)
print('--- cadence auto adjust ---')
dump(1246,1260)
print('--- walk pulse + sharding ---')
dump(1984,2050)
print('--- plateau/thermo/cadence ---')
dump(2072,2097)
print('--- ctrl logging ---')
dump(2174,2180)
