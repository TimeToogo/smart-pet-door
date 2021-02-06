import sys
import colorsys
from .annotator import Annotator
from config import config

if len(sys.argv) < 3:
    print('usage: python -m src.ml.run_annotator [video dir] [out dir]')
    sys.exit(1)


labels = []
h = 0
s = 100
l = 0

def rgb(h, s, l):
    (r, g, b) = colorsys.hsv_to_rgb(h / 360, s / 100, l / 100)
    return (int(r * 255), int(g * 255), int(b * 255))

for key, _class in config.VC_PET_CLASSES.items():
    l = 50
    for ekey, eclass in config.VC_EVENT_CLASSES.items():
        l += 10
        labels.append({'name': key + '_' + ekey, 'color': rgb(h, s, l)})
    h += 40

key, _class = next(iter(config.VC_PET_CLASSES.items()))
for okey, oclass in config.VC_PET_CLASSES.items():
    if okey == key:
        continue

    pets = key + '_' + okey
    h += 20
    l = 20
    for ekey, eclass in config.VC_EVENT_CLASSES.items():
        l += 10
        labels.append({'name': pets + '_' + ekey, 'color': rgb(h, s, l)})

labels.append({'name': 'DISCARD', 'color': (0, 0, 0)})

# Initialise MuViLab
clips_folder = sys.argv[1]
annotator = Annotator(labels, clips_folder, annotation_file=sys.argv[2] + '/labels.json', N_show_approx=16)

# Run the GUI
annotator.main()