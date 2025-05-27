#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module to preprocess HalfPipe output files.
"""
import os
import logging
import glob
import re
import pandas as pd
from src.cleaner import Cleaner

class Preprocessor:
    """Class to preprocess HalfPipe output files"""
    
    def __init__(self, halfipe_output_dir:str='/data', atlas_dir:str='/data/atlas'):
        """Initialize the Preprocessor by checking HalfPipe output directory."""
        if not self.check_halfpipe_output_dir(halfipe_output_dir):
            raise FileExistsError(f"HalfPipe output directory {halfipe_output_dir} does not exist or is empty.")
        self.halfipe_output_dir = halfipe_output_dir
        self.atlas_dir = atlas_dir
    

    def check_halfpipe_output_dir(self, halfipe_output_dir) -> bool:
        """Check if the HalfPipe output directory exists and is not empty"""
        if not os.path.exists(halfipe_output_dir):
            logging.error(f"HalfPipe output directory {halfipe_output_dir} does not exist.")
            return False
        elif not os.listdir(halfipe_output_dir):
            logging.error(f"HalfPipe output directory {halfipe_output_dir} is empty.")
            return False
        logging.debug(f"HalfPipe output directory {halfipe_output_dir} is valid.")
        return True


    def get_all_halfpipe_timeseries_paths(self) -> list:
        """Extract all time series TSV path from input directory"""
        timeseries_path_pattern = os.path.join(self.halfipe_output_dir, '**', '*_timeseries.tsv')
        return glob.glob(timeseries_path_pattern, recursive=True)


    def extract_metadata_from_timeseries(self, timeseries_path: str) -> tuple:
        """Extract subject, session, task, run, strategy, and atlas from the timeseries path"""
        subjects, sessions, tasks, runs, strategies, atlases = [], [], [], [], [], []
        for path in timeseries_path:
            subject_match = re.search(r'/(?:sub-([^/]+))', path)
            session_match = re.search(r'/(?:ses-([^/]+))', path)
            task_match = re.search(r'/(?:task-([^/]+))', path)
            run_match = re.search(r'/(?:run-([^/]+))', path)
            strategy_match = re.search(r'(?:feature-([^_]+))', path)
            atlas_match = re.search(r'(?:atlas-([^_]+))', path) 

            if subject_match: subjects.append(subject_match.group(1))
            if session_match: sessions.append(session_match.group(1))
            if task_match: tasks.append(task_match.group(1))
            if run_match: runs.append(run_match.group(1))
            if strategy_match: strategies.append(strategy_match.group(1))
            if atlas_match: atlases.append(atlas_match.group(1))
        
        subjects = list(set(subjects))
        sessions = list(set(sessions))
        tasks = list(set(tasks))
        runs = list(set(runs))
        strategies = list(set(strategies))
        atlases = list(set(atlases))

        return subjects, sessions, tasks, runs, strategies, atlases


    def get_atlases_labels(self) -> dict:
        """Get labels for atlases from the atlas directory"""
        atlases_labels = {}
        atlas_files = glob.glob(os.path.join(self.atlas_dir, 'atlas-*.tsv'))
        for atlas_file in atlas_files:
            logging.debug(f"Reading atlas file: {atlas_file}")
            atlas_name = os.path.basename(atlas_file).split('.')[0].split('-')[1].split('_')[0]
            atlas_labels = pd.read_csv(atlas_file, sep='\t', header=None)[1].tolist()
            if len(atlas_labels) > 0:
                atlases_labels[atlas_name] = atlas_labels
        return atlases_labels

    def clean_timeseries(self, subjects: list, sessions: list, tasks: list, runs: list, strategies: list, atlases: list, atlases_labels:dict) -> None:
        """Clean the timeseries data by removing NaN values"""
        for atlas in atlases:
            logging.info(f"Cleaning timeseries for atlas: {atlas}")
            atlas_labels = atlases_labels.get('Schaefer2018Combined', [])   # TODO: replace with : atlases_labels.get(atlas, [])
            for strategy in strategies:
                logging.info(f"Cleaning timeseries for strategy: {strategy}")
                for task in tasks:
                    logging.info(f"Cleaning timeseries for task: {task}")
                    if len(sessions) == 0:
                        sessions = ['default']
                    for session in sessions:
                        logging.info(f"Cleaning timeseries for session: {session}")
                        if len(runs) == 0:
                            runs = ['default']
                        for run in runs:
                            logging.info(f"Cleaning timeseries for run: {run}")
                            cleaner = Cleaner(subjects, run, session, task, strategy, atlas, atlas_labels, self.halfipe_output_dir)
                            cleaner.clean_dataset()


    def run(self):
        """Run the preprocessor"""
        logging.info("Preprocessing HalfPipe output timeseries...")
        timeseries_paths = self.get_all_halfpipe_timeseries_paths()
        if not timeseries_paths:
            raise FileNotFoundError("No HalfPipe timeseries files found.")
        subjects, sessions, tasks, runs, strategies, atlases = self.extract_metadata_from_timeseries(timeseries_paths)
        if not subjects:
            raise ValueError("No subjects found in the HalfPipe timeseries files.")
        logging.info(f"Extracted metadata: {len(subjects)} subjects, {max(len(sessions), 1)} sessions, {max(len(tasks), 1)} tasks, {max(len(runs), 1)} runs, {len(strategies)} strategies, {len(atlases)} atlases.")
        atlases_labels = self.get_atlases_labels()
        logging.info(f"{len(atlases_labels)} atlases and their labels found.")
        cleaned_timeseries = self.clean_timeseries(subjects, sessions, tasks, runs, strategies, atlases, atlases_labels)
        logging.info("Preprocessing completed.")
        
        