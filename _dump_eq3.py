from pathlib import Path
path = Path('G:/AI/mirror/VRAXION/tournament_phase6.py')
lines = path.read_text().splitlines()

def dump(a,b):
    for i in range(a,b+1):
        if 1 <= i <= len(lines):
            print(f'{i:04d}: {lines[i-1]}')

print('--- pointer update core ---')
dump(1070,1140)
