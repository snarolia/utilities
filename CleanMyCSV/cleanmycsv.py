import pandas as pd
import numpy as np
import argparse

NULL_VALUES = ['null', 'n/a', 'na', "-", " ", "", "N/A", "NULL"]

def clean_csv(input_file, output_file, log_file=None):
    df = pd.read_csv(input_file)

    original_shape = df.shape
    