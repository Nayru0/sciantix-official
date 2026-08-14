"""
sciantix regression suite
author: Giovanni Zullo
"""

import json

import numpy as np

class SciantixOutput:
    def __init__(self, path):

        raw = np.genfromtxt(
            path,
            delimiter='\t',
            dtype=str,
            filling_values="nan",
            autostrip=True
        )


        if raw.ndim == 1:
            raw = np.array([raw])

        cleaned = []
        for row in raw:
            if any(cell.strip() != "" for cell in row):
                cleaned.append(row)

        cleaned = np.array(cleaned, dtype=str)

        self.header = cleaned[0]

        data = []
        for row in cleaned[1:]:
            vals = []
            for cell in row:
                try:
                    vals.append(float(cell))
                except:
                    vals.append(np.nan)
            data.append(vals)

        self.data = np.array(data, dtype=float)
        self.colmap = {name: i for i, name in enumerate(self.header)}

    def get_last(self, var: str) -> float:
        return self.data[-1, self.colmap[var]]

    def get_all(self, var: str):
        return self.data[:, self.colmap[var]]

class SciantixOutputJson:
    def __init__(self, path):

        with open(path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
            self.case_id = self.data.get("caseId", "")
            self.quantities = {}
            self.values = np.array(self.data.get("table",{}).get("rows",[]), dtype=float)
            for i in range(len(self.data.get("table",{}).get("columns",[]))):
                self.quantities[self.data["table"]["columns"][i]["label"]] = self.data["table"]["columns"][i]["index"]

    def get_last(self, quantity: str) -> float:
        return self.values[-1][self.quantities[quantity]]

    def get_all(self, quantity: str):
        return self.values[:, self.quantities[quantity]]
        

