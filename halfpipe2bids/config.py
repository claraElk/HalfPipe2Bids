# config.py

import os

# Paths
PATH_HALFPIPE = 'halfpipe2bids/tests/data/dataset-ds000030_halfpipe1.2.3dev'
PATH_ATLAS = 'data/atlas'
OUTPUT_PATH = 'output/BEP017'


PATH_DERIVATIVES = os.path.join(PATH_HALFPIPE, 'derivatives')
PATH_HALFPIPE_TIMESERIES = os.path.join(PATH_DERIVATIVES, 'halfpipe')
PATH_FMRIPREP_CONFOUNDS = os.path.join(PATH_DERIVATIVES, 'fmriprep')

PATH_LABEL_SCHAEFER = os.path.join(PATH_ATLAS, 'atlas-Schaefer2018Combined_dseg.tsv')
PATH_SPEC = os.path.join(PATH_HALFPIPE, 'spec.json')


# Atlas
NAME_ATLAS = 'schaefer400'  # doit être aligné avec le fichier de labels

# Task
TASK = 'task-rest'

# Autres
NUM_RUN = '1'