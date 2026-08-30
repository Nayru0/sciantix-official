"""
sciantix regression suite
author: Giovanni Zullo
"""

import json

import numpy as np

class SciantixOutput:
    def __init__(self, path):

        with open(path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
            self.case_id = self.data.get("caseId", "")
            self.quantities = {}
            self.header = []
            self.values = np.array(self.data.get("table",{}).get("rows",[]), dtype=float)
            for i in range(len(self.data.get("table",{}).get("columns",[]))):
                self.quantities[self.data["table"]["columns"][i]["label"]] = self.data["table"]["columns"][i]["index"]
                self.header.append(self.data["table"]["columns"][i]["label"])

    def get_last(self, quantity: str) -> float:
        return self.values[-1][self.quantities[quantity]]

    def get_all(self, quantity: str):
        return self.values[:, self.quantities[quantity]]
        

