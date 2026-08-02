#!/usr/bin/env python3
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from regression.core.common import load_output, load_gold
from regression.core.plot import parity_plot
from regression.core.report import generate_html_report
from regression.core.multireport import generate_html_multireport


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
            if parts[col_index] == "/":
                values.append(np.nan)
            else:
                values.append(float(parts[col_index])) 

    return np.array(names), np.array(values)


# ------------------------------------------------------------
# parity_plot function
# ------------------------------------------------------------
def parity_plot_white(col_out, col_exp,multireport=False):

    root = os.path.dirname(__file__)
    white_root = os.path.abspath(os.path.join(root, "..", "white"))
    outdir = os.path.join(root, "figures")
    os.makedirs(outdir, exist_ok=True)

    # load experimental data
    exp_names, exp_values = load_experimental("white_data.txt",col_exp)

    exp_list, gold_list, test_list = [], [], []
    test_names = []

    # loop over test directories
    for name in sorted(os.listdir(white_root)):
        if not name.startswith("test_White"):
            continue

        case = os.path.join(white_root, name)
        if not os.path.isdir(case):
            continue

        test_name = name  # matching by string
        test_names.append(test_name)

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
    parity_plot(exp_arr, gold_arr, test_arr, f"white_{col_exp.replace(' ', '_').replace('/','')}", f"White – {col_exp}", outdir)
    print(f"""Plotted {col_exp}""")

    #Calculating the error
    acceptability_range = 0.5 #50% of the experimental value
    
    error_test = test_arr - exp_arr
    error_gold = gold_arr - exp_arr
    error_output = test_arr - gold_arr

    if not multireport:
        # --------------------
        # Statistical analysis
        # --------------------
        print("\n" + "="*50)
        print(f"STATISTICAL ANALYSIS - {col_exp}")
        print("="*50)

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
        print(f"Current SCIANTIX  - RMSE:   {(np.sqrt(np.mean((error_test/exp_arr)**2)))*100:.4f}%")
        print(f"Current SCIANTIX  - MAD:    {np.median(np.abs(error_test/exp_arr))*100:.4f}%")
        print(f"Current SCIANTIX  - max error:   {np.max(np.abs(error_test/exp_arr))*100:.4f}%")
        print("-" * 30)

        # Gold results
        print(f"Gold (reference)  - mean:   {np.mean(gold_arr):.4f}")
        print(f"Gold (reference)  - median: {np.median(gold_arr):.4f}")
        print(f"Gold (reference)  - MAD:    {np.median(np.abs(error_gold)):.4f}")
        print(f"Gold (reference)  - RMSE:   {np.sqrt(np.mean(error_gold**2)):.4f}")
        print(f"Gold (reference)  - max error:   {np.max(np.abs(error_gold/exp_arr))*100:.4f}%")
        print("="*50 + "\n")

        #Generating an html report for only one physical quantity
        results = []
        for i in range(len(test_arr)):
            ok = abs(error_test[i]) <= exp_arr[i]*acceptability_range #Condition for the test to be considered as passed
            message = ""
            if abs(error_output[i]) > test_arr[i]*0.1:
                message = f"Value different from gold case by more than 10%"
            results.append((test_names[i],ok,message))

        outdir = os.path.join(root, "figures")
        generate_html_report(results, outdir)

        for i in range(len(error_output)):
            if abs(error_output[i]) > test_arr[i]*0.1:
                print(f"[WARNING] Large deviation for {test_names[i]} : Error : {error_output[i]:.4f}, Value (test) : {test_arr[i]:.4f}, Value (gold) : {gold_arr[i]:.4f}")
        print(f"Tested value : {col_exp} (experimental) vs {col_out} (SCIANTIX output)")
        print(f"\nAcceptability range : ±{acceptability_range*100:.0f}% of the experimental value")

    else:
        #In case of multireport, we return the results for each test case given a physical quantity
        ok_flags = []
        for i in range(len(test_arr)):
            if abs(error_test[i]) > exp_arr[i]*acceptability_range:
                ok_flags.append(False)
            else:
                ok_flags.append(True)
        return test_names, ok_flags


def main():
    multireport = True
    root = os.path.dirname(__file__)
    outdir = os.path.join(root, "figures")
    #Change the column name depending on which value to compare
    col_out = "Intergranular bubble concentration (bub/m2)" #Name of the column in the output file
    col_exp = "Bubble Density (m-2)" #Name of the column in the experimental file
    #You can find the reference column names in white/data/whitedata_format.txt and white/data/output_format.txt
    
    if not multireport:
        parity_plot_white(col_out, col_exp)
    else:
        #Lists of physical quantities to compare
        list_col_out = ["Intergranular bubble concentration (bub/m2)","Intergranular gas swelling (/)","Intergranular fractional coverage (/)","Intergranular bubble radius (m)"]
        list_col_exp = ["Bubble Density (m-2)","Intergranular Swelling (/)","Grain Face Coverage by Porosity (/)","Projected Radius (m)"]
        
        accumulated_results = {}
        results = []
        test_names = []
        for col_out, col_exp in zip(list_col_out, list_col_exp):
            names, ok_flags = parity_plot_white(col_out, col_exp, multireport=True)
            if test_names == []:
                test_names = names
            for name, ok in zip(names, ok_flags):
                if name not in accumulated_results:
                    accumulated_results[name] = []
                accumulated_results[name].append(ok)

        for name in test_names:
            ok_list = accumulated_results[name]
            message = ""
            if not all(ok_list):
                message = f"Failed for at least one physical quantity"
            results.append((name, ok_list, message))

        generate_html_multireport(results, list_col_exp, outdir)

if __name__ == "__main__":
    main()