# functions.py

import os
import json
import pandas as pd
import numpy as np
import logging
from nilearn.signal import clean
from nilearn import plotting


def get_subjects(path_halfpipe_timeseries):
    return [sub for sub in os.listdir(path_halfpipe_timeseries)
            if os.path.isdir(os.path.join(path_halfpipe_timeseries, sub))]


def load_label_schaefer(path_label_schaefer):
    return list(pd.read_csv(path_label_schaefer, sep='\t', header=None)[1])


def get_strategy_confounds(spec_path):
    with open(spec_path, "r") as f:
        data = json.load(f)

    setting_to_confounds = {
        s["name"]: s.get("confounds_removal", [])
        for s in data.get("settings", [])
    }

    strategy_confounds = {}
    for feature in data.get("features", []):
        strategy_name = feature.get("name")
        setting_name = feature.get("setting")
        strategy_confounds[strategy_name] = setting_to_confounds.get(setting_name, [])

    return strategy_confounds


def impute_and_clean(df):
    row_means = df.mean(axis=1, skipna=True)
    df_filled = df.T.fillna(row_means).T

    if df_filled.isna().any().any():
        logging.warning("Certaines valeurs n'ont pas pu être imputées.")

    cleaned = clean(df_filled.values, detrend=True, standardize='zscore_sample')
    return pd.DataFrame(cleaned, columns=df.columns, index=df.index)


def remove_bad_rois(dict_timeseries, label_schaefer, threshold=0.5):
    nan_counts = {label: 0 for label in label_schaefer}
    total_subjects = len(dict_timeseries)

    for df in dict_timeseries.values():
        for label in label_schaefer:
            if label in df.columns and df[label].isna().all():
                nan_counts[label] += 1

    df_nan_prop = pd.DataFrame({
        "ROI": list(nan_counts.keys()),
        "proportion_nan": [nan_counts[label] / total_subjects for label in label_schaefer]
    })

    labels_to_drop = df_nan_prop[df_nan_prop["proportion_nan"] > threshold]["ROI"].tolist()

    for key in dict_timeseries:
        dict_timeseries[key] = dict_timeseries[key].drop(columns=labels_to_drop, errors='ignore')

    return labels_to_drop


def get_coords(volume_path, label_schaefer, labels_to_drop):
    coords = plotting.find_parcellation_cut_coords(volume_path)
    df_coords = pd.DataFrame(coords, index=label_schaefer, columns=['x', 'y', 'z'])
    return df_coords[~df_coords.index.isin(labels_to_drop)]