# main.py

import os
import json
import pandas as pd

from config import *
from functions import *

label_schaefer = load_label_schaefer(PATH_LABEL_SCHAEFER)
sujets = get_subjects(PATH_HALFPIPE_TIMESERIES)
strategy_confounds = get_strategy_confounds(PATH_SPEC)

volume_path = os.path.join(PATH_ATLAS, 'atlas-Schaefer2018Combined_dseg.nii.gz')

for strategy in strategy_confounds.keys():
    print(f"\n>>> Traitement de la stratégie : {strategy}")

    dict_timeseries = {}
    dict_clean_timeseries = {}
    dict_samplingfrequency = {}
    missing_list = []
    dict_mean_framewise = {}
    dict_scrubvolume = {}

    for sub in sujets:
        try:
            timeseries_path = f'{PATH_HALFPIPE_TIMESERIES}/{sub}/func/task-rest/{sub}_{TASK}_feature-{strategy}_atlas-{NAME_ATLAS}_timeseries.tsv'
            json_path = f'{PATH_HALFPIPE_TIMESERIES}/{sub}/func/task-rest/{sub}_{TASK}_feature-{strategy}_atlas-{NAME_ATLAS}_timeseries.json'
            confounds_path = f'{PATH_FMRIPREP_CONFOUNDS}/{sub}/func/{sub}_{TASK}_desc-confounds_timeseries.tsv'

            df_timeseries = pd.read_csv(timeseries_path, sep='\t', header=None)
            df_timeseries.columns = label_schaefer
            dict_timeseries[sub] = df_timeseries

            df_confounds = pd.read_csv(confounds_path, sep='\t')
            dict_mean_framewise[sub] = df_confounds['framewise_displacement'].mean()
            dict_scrubvolume[sub] = df_confounds.filter(like='motion_outlier').shape[1]

            with open(json_path) as f:
                meta = json.load(f)
            dict_samplingfrequency[sub] = meta.get("SamplingFrequency", None)

        except FileNotFoundError:
            missing_list.append(sub)

    labels_to_drop = remove_bad_rois(dict_timeseries, label_schaefer)
    remaining_labels = list(set(label_schaefer) - set(labels_to_drop))

    for sub in dict_timeseries:
        dict_clean_timeseries[sub] = impute_and_clean(dict_timeseries[sub])

    dict_corr = {
        sub: dict_clean_timeseries[sub].corr(method='pearson')
        for sub in dict_clean_timeseries
    }

    nroi = len(remaining_labels)
    regressors = strategy_confounds[strategy]

    for sub in dict_clean_timeseries:
        base_name = f"{sub}_{TASK}_seg-{NAME_ATLAS}{nroi}_desc-denoise{strategy}"

        # Time series
        ts_path = os.path.join(OUTPUT_PATH, sub, 'func', f"{base_name}_timeseries.tsv")
        os.makedirs(os.path.dirname(ts_path), exist_ok=True)
        dict_clean_timeseries[sub].columns = range(nroi)
        dict_clean_timeseries[sub].to_csv(ts_path, sep='\t', index=False)

        # Connectivity
        conn_path = os.path.join(OUTPUT_PATH, sub, 'func', f"{base_name}_meas-PearsonCorrelation_relmat.tsv")
        dict_corr[sub].columns = range(nroi)
        dict_corr[sub].to_csv(conn_path, sep='\t', index=False)

        # JSON sidecar
        json_data = {
            "ConfoundRegressors": regressors,
            "NumberOfVolumesDiscardedByMotionScrubbing": dict_scrubvolume[sub],
            "MeanFramewiseDisplacement": dict_mean_framewise[sub],
            "SamplingFrequency": dict_samplingfrequency[sub]
        }
        json_path = os.path.join(OUTPUT_PATH, sub, 'func', f"{base_name}_timeseries.json")
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=4)

# Export du fichier JSON commun de matrice
summary_path = os.path.join(OUTPUT_PATH, 'meas-PearsonCorrelation_relmat.json')
with open(summary_path, 'w') as f:
    json.dump({
        "Measure": "Pearson correlation",
        "MeasureDescription": "Pearson correlation",
        "Weighted": False,
        "Directed": False,
        "ValidDiagonal": True,
        "StorageFormat": "Full",
        "NonNegative": "",
        "Code": "https://github.com/pbergeret12/HalfPipe2Bids/tree/main"
    }, f, indent=4)

print(f"Export terminé dans : {OUTPUT_PATH}")

# Export du json de description de dataset

json_dataset_description = {
    "BIDSVersion": "1.9.0",
    "License": None,
    "Name": None,
    "ReferencesAndLinks": [],
    "DatasetDOI": None,
    "DatasetType": "derivative",
    "GeneratedBy": [
        {
            "Name": "Halfpipe2Bids",
            "Version": "0.1",
            "CodeURL": "https://github.com/pbergeret12/HalfPipe2Bids/tree/main"
        }
    ],
    "HowToAcknowledge": "Please refer to our repository: https://github.com/pbergeret12/HalfPipe2Bids/tree/main."
}

output_filename = 'dataset_description.json'
output_file = os.path.join(OUTPUT_PATH, output_filename)

# Exporter le JSON
with open(output_file, 'w') as f:
    json.dump(json_dataset_description, f, indent=4)

print(f"JSON exporté vers {OUTPUT_PATH}")
