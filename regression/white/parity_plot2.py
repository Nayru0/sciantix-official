#!/usr/bin/env python3
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from regression.core.common import load_output, load_gold
from regression.core.plot import parity_plot


# ------------------------------------------------------------
# utils
# ------------------------------------------------------------
def extract_last(output, column):
    """Return the last timestep value of a given column."""
    header = [h.strip() for h in output.header]
    if column not in header:
        raise KeyError(f"Column '{column}' not found in output.header")
    idx = header.index(column)
    return output.data[-1, idx]


def load_experimental(basename,col_name):
    """
    Load experimental data for White.
    Format: test_name   ... col_name    ...
    Tabular with header_line
    """
    root = os.path.dirname(__file__)
    fpath = os.path.join(root, "data", basename)

    names = []
    values = []

    with open(fpath, "r") as f:
        #Finding col_name (matching the strings)
        header_line = f.readline()
        if not header_line:
            raise ValueError(f"File {basename} is empty.")
            
        headers = header_line.strip().split("\t")
        
        if col_name not in headers:
            raise ValueError(f"Unable to find '{col_name}' in file. Available columns : {headers}")
            
        col_index = headers.index(col_name)

        for line in f:
            if not line.strip():
                continue
            parts = line.strip().split()
            
            #For an incomplete line
            if len(parts) <= col_index:
                continue
                
            names.append(parts[0])
            values.append(float(parts[col_index])) 

    return np.array(names), np.array(values)


# ------------------------------------------------------------
# main
# ------------------------------------------------------------
def main():

    root = os.path.dirname(__file__)
    white_root = os.path.abspath(os.path.join(root, "..", "white"))
    outdir = os.path.join(root, "figures")
    os.makedirs(outdir, exist_ok=True)

    #Change the column name depending on which value to compare
    col_out = "Intergranular gas swelling (/)" #Name of the column in the output file
    col_exp = "Intergranular Swelling (/)" #Name of the column in the experimental file
    #You can find the reference column names in white/data/whitedata_format.txt and white/data/output_format.txt

    # load experimental swelling
    exp_names, exp_values = load_experimental("white_data.txt",col_exp)

    exp_list, gold_list, test_list = [], [], []

    # loop over test directories
    for name in sorted(os.listdir(white_root)):
        if not name.startswith("test_White"):
            continue

        case = os.path.join(white_root, name)
        if not os.path.isdir(case):
            continue

        test_name = name  # matching by string

        # find experimental value
        idx = np.where(exp_names == test_name)[0]
        if len(idx) == 0:
            print(f"[WARNING] No experimental {col_exp} for {test_name}")
            continue

        exp_val = exp_values[idx][0]

        # load sciantix outputs
        out = load_output(case)
        gold = load_gold(case)

        data_test = extract_last(out, col_out)
        data_gold = extract_last(gold, col_out)

        exp_list.append(exp_val)
        gold_list.append(data_gold)
        test_list.append(data_test)

    # convert to arrays
    exp_arr = np.array(exp_list)
    gold_arr = np.array(gold_list)
    test_arr = np.array(test_list)

    # plot
    parity_plot(exp_arr, gold_arr, test_arr, "white_swelling", f"White – {col_exp}", outdir)

    # --------------------
    # Statistical analysis
    # --------------------
    print("\n" + "="*50)
    print("STATISTICAL ANALYSIS")
    print("="*50)

    error_test = test_arr - exp_arr
    error_gold = gold_arr - exp_arr

    # Experimental data
    print(f"Experimental data - mean:   {np.mean(exp_arr):.4f}")
    print(f"Experimental data - median: {np.median(exp_arr):.4f}")
    print(f"Experimental data - Q1:     {np.percentile(exp_arr, 25, method='midpoint'):.4f}")
    print(f"Experimental data - Q3:     {np.percentile(exp_arr, 75, method='midpoint'):.4f}")
    print("-" * 30)

    # Current results (test)
    print(f"Current SCIANTIX  - mean:   {np.mean(test_arr):.4f}")
    print(f"Current SCIANTIX  - median: {np.median(test_arr):.4f}")
    print(f"Current SCIANTIX  - Q1:     {np.percentile(test_arr, 25, method='midpoint'):.4f}")
    print(f"Current SCIANTIX  - Q3:     {np.percentile(test_arr, 75, method='midpoint'):.4f}")
    print(f"Current SCIANTIX  - BIAS:   {np.median(error_test):.4f}")
    print(f"Current SCIANTIX  - RMSE:   {np.sqrt(np.mean(error_test**2)):.4f}")
    print(f"Current SCIANTIX  - MAD:    {np.median(np.abs(error_test)):.4f}")
    print("-" * 30)

    # Gold results
    print(f"Gold (reference)  - mean:   {np.mean(gold_arr):.4f}")
    print(f"Gold (reference)  - median: {np.median(gold_arr):.4f}")
    print(f"Gold (reference)  - MAD:    {np.median(np.abs(error_gold)):.4f}")
    print(f"Gold (reference)  - RMSE:   {np.sqrt(np.mean(error_gold**2)):.4f}")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
