#!/usr/bin/env python3
import os
import sys
import numpy as np
import json
import matplotlib.pyplot as plt
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from regression.core.common import load_output, load_gold, load_output_json, load_gold_json
from regression.core.plot import parity_plot
from regression.core.report import generate_html_report
from regression.core.multireport import generate_html_multireport


# ------------------------------------------------------------
# utils
# ------------------------------------------------------------
def load_experimental_json(basename,quantity):
    """
    Load experimental data for a specified quantity from White in JSON format
    Return numpy arrays of test names and corresponding values and the unit of the quantity.
    """
    root = os.path.dirname(__file__)
    fpath = os.path.join(root, "metadata\\experimental", basename)

    names = []
    values = []
    unit = ""

    with open(fpath, "r") as f:
        #Load the JSON data
        data = json.load(f)
        measurements = data.get("measurement", [])

        if not measurements:
            raise ValueError(f"No measurements found in file {basename}.")

        for measurement in measurements:
            if measurement.get("quantity") == quantity:
                names.append(measurement.get("caseId"))
                values.append(measurement.get("value"))
                unit = measurement.get("unit", "")

    if not names:
        raise ValueError(f"No measurements found for quantity '{quantity}' in file {basename}.")
    return np.array(names), np.array(values), unit


def statistical_analysis(exp_arr, test_arr, gold_arr, quantity, exp_unit):
    error_test = test_arr - exp_arr
    error_gold = gold_arr - exp_arr
    error_output = test_arr - gold_arr
    # --------------------
    # Statistical analysis
    # --------------------
    print("\n" + "="*50)
    print(f"STATISTICAL ANALYSIS - {quantity}")
    print("="*50)

    # Experimental data
    print(f"Experimental data - mean:   {np.mean(exp_arr):.4f} {exp_unit}")
    print(f"Experimental data - median: {np.median(exp_arr):.4f} {exp_unit}")
    print(f"Experimental data - Q1:     {np.percentile(exp_arr, 25, method='midpoint'):.4f} {exp_unit}")
    print(f"Experimental data - Q3:     {np.percentile(exp_arr, 75, method='midpoint'):.4f} {exp_unit}")
    print("-" * 30)

    # Current results (test)
    print(f"Current SCIANTIX  - mean:   {np.mean(test_arr):.4f} {exp_unit}")
    print(f"Current SCIANTIX  - median: {np.median(test_arr):.4f} {exp_unit}")
    print(f"Current SCIANTIX  - Q1:     {np.percentile(test_arr, 25, method='midpoint'):.4f} {exp_unit}")
    print(f"Current SCIANTIX  - Q3:     {np.percentile(test_arr, 75, method='midpoint'):.4f} {exp_unit}")
    print(f"Current SCIANTIX  - BIAS:   {np.median(error_test):.4f} {exp_unit}")
    print(f"Current SCIANTIX  - RMSE:   {(np.sqrt(np.mean((error_test/exp_arr)**2)))*100:.4f} %")
    print(f"Current SCIANTIX  - MAD:    {np.median(np.abs(error_test/exp_arr))*100:.4f} %")
    print(f"Current SCIANTIX  - max error:   {np.max(np.abs(error_test/exp_arr))*100:.4f} %")
    print("-" * 30)

    # Gold results
    print(f"Gold (reference)  - mean:   {np.mean(gold_arr):.4f} {exp_unit}")
    print(f"Gold (reference)  - median: {np.median(gold_arr):.4f} {exp_unit}")
    print(f"Gold (reference)  - MAD:    {np.median(np.abs(error_gold)):.4f} {exp_unit}")
    print(f"Gold (reference)  - RMSE:   {np.sqrt(np.mean(error_gold**2)):.4f} {exp_unit}")
    print(f"Gold (reference)  - max error:   {np.max(np.abs(error_gold/exp_arr))*100:.4f} %")
    print("="*50 + "\n")    
# ------------------------------------------------------------
# parity_plot function
# ------------------------------------------------------------
def parity_plot_white(quantity, multireport=False):

    root = os.path.dirname(__file__)
    white_root = os.path.abspath(os.path.join(root, "..", "white"))
    outdir = os.path.join(root, "figures")
    os.makedirs(outdir, exist_ok=True)

    # load experimental data
    exp_names, exp_values, exp_unit = load_experimental_json("white_experimental_measurements.jsonld",quantity)

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
            print(f"[WARNING] No experimental {quantity} for {test_name}")
            continue

        exp_val = exp_values[idx][0]

        # load sciantix outputs
        out = load_output_json(case)
        gold = load_gold_json(case)

        data_test = out.get_last(quantity)
        data_gold = gold.get_last(quantity)

        exp_list.append(exp_val)
        gold_list.append(data_gold)
        test_list.append(data_test)

    # convert to arrays
    exp_arr = np.array(exp_list)
    gold_arr = np.array(gold_list)
    test_arr = np.array(test_list)

    # plot
    parity_plot(exp_arr, gold_arr, test_arr, f"white_{quantity.replace(' ', '_')}", f"White – {quantity} ({exp_unit})", outdir)
    print(f"""Plotted {quantity}""")

    #Calculating the error
    acceptability_range = 0.5 #50% of the experimental value
    
    error_test = test_arr - exp_arr
    error_gold = gold_arr - exp_arr
    error_output = test_arr - gold_arr

    if not multireport:
        #Statistical analysis for the current physical quantity
        statistical_analysis(exp_arr, test_arr, gold_arr, quantity, exp_unit)

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
        print(f"Tested value : {quantity} ({exp_unit})")
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

def do_multireport(quantities,outdir):
    accumulated_results = {}
    results = []
    test_names = []
    for quantity in quantities :
        names, ok_flags = parity_plot_white(quantity, multireport=True)
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

    generate_html_multireport(results, quantities, outdir)

def main():
    multireport = False
    root = os.path.dirname(__file__)
    outdir = os.path.join(root, "figures")
    #Change the name depending on which quantity to compare
    quantity = "Intergranular bubble concentration"
    #You can find the names of the quantities in metadata/variable/sciantix_variable_catalog.jsonld
    #or in the output.txt file of each test case

    if not multireport:
        parity_plot_white(quantity)
    else:
        #Lists of physical quantities to compare
        quantities = ["Intergranular bubble concentration","Intergranular gas swelling","Intergranular fractional coverage","Intergranular bubble radius"]
        do_multireport(quantities, outdir)

if __name__ == "__main__":
    main()