#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module to clean timeseeries data.
"""

import os
import logging
import glob
import pandas as pd

class Cleaner:
    """Class to clean time series data"""

    def __init__(self, subjects: list, run:str, session:str, task:str, strategy, atlas:str, atlas_labels:list, data_dir:str='/data') -> None:
        """Initialize the Cleaner class."""
        self.data_dir = data_dir
        self.subjects = subjects
        self.run = run if run != 'default' else None
        self.session = session if session != 'default' else None
        self.task = task
        self.strategy = strategy
        self.atlas = atlas
        self.atlas_labels = atlas_labels
        self.timeseries_per_subject = {}
        self.timeseries_not_found = []
    
    def get_timeseries(self) -> None:
        """Get the timeseries data for each subject"""
        for subject in self.subjects:
            timeseries_filename = f"sub-{subject}_task-{self.task}{'_run-' + self.run if self.run else ''}_feature-{self.strategy}_atlas-{self.atlas}_timeseries.tsv"
            timeseries_partial_path = f"sub-{subject}{'/ses-' + self.session if self.session else ''}/func/**/{timeseries_filename}"
            timeseries_full_path = os.path.join(self.data_dir, '**', timeseries_partial_path)
            try :
                df_timeseries = pd.read_csv(glob.glob(timeseries_full_path, recursive=True)[0], sep='\t', header=None)
                df_timeseries.columns = self.atlas_labels
                self.timeseries_per_subject[subject] = df_timeseries
            except FileNotFoundError:
                self.timeseries_not_found.append(subject)
                logging.warning(f"File not found for subject {subject}: {timeseries_partial_path}")
    
    def compute_na_ratio_per_label(self) -> pd.DataFrame:
        """Compute ratio of NA values per label"""
        na_counts = {label: 0 for label in self.atlas_labels}
        for _, df in self.timeseries_per_subject.items():
            for label in self.atlas_labels:
                if label in df.columns and df[label].isna().all():
                    na_counts[label] += 1
        return pd.DataFrame({
            "roi": list(na_counts.keys()),
            "na_ratio": [na_counts[label] / len(self.timeseries_per_subject) for label in na_counts.keys()],
        })
    
    def remove_labels(self, labels: list) -> None:
        """Remove labels from the timeseries data"""
        for subject, df in self.timeseries_per_subject.items():
            self.timeseries_per_subject[subject] = df.drop(columns=labels, errors='ignore')
    
    def compute_na_ratio_per_subject(self) -> pd.DataFrame:
        """Compute ratio of NA values per subject"""
        na_ratios = []
        for subject, df in self.timeseries_per_subject.items():
            total_roi = df.shape[1]
            roi_nan = df.isna().any().sum()
            na_ratio = roi_nan / total_roi if total_roi > 0 else 0
            na_ratios.append({
                "subject": subject,
                "na_ratio": na_ratio,
            })
        return pd.DataFrame(na_ratios)
    
    def remove_subjects(self, subjects:list) -> None:
        """Remove subjects from the timeseries data"""
        for subject in subjects:
            if subject in self.timeseries_per_subject:
                del self.timeseries_per_subject[subject]

   
    def clean_dataset(self) -> None:
        """Clean the dataset"""
        self.get_timeseries()
        df_na_ratio_labels = self.compute_na_ratio_per_label()
        labels_to_remove = df_na_ratio_labels[df_na_ratio_labels['na_ratio'] > 0.5]['roi'].tolist()
        logging.debug(f"{len(labels_to_remove)} labels to remove")
        self.remove_labels(labels_to_remove)
        df_na_ratio_subjects = self.compute_na_ratio_per_subject()
        subjects_to_remove = df_na_ratio_subjects[df_na_ratio_subjects['na_ratio'] > 0.2]['subject'].tolist()
        logging.debug(f"{len(subjects_to_remove)} subjects to remove")
        self.remove_subjects(subjects_to_remove)


