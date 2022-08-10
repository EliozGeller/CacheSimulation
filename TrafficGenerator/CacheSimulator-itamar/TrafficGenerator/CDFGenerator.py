import pandas as pd
import numpy as np


class Utils(object):
    @staticmethod
    def search_interval_array(interval_dict, value):
        interval_array = list(interval_dict.keys())
        low, high = 0, len(interval_array) - 1
        while low <= high:
            mid = int((high + low) / 2)
            if value in interval_array[mid]:
                return interval_dict[interval_array[mid]]
            if value < interval_array[mid].right:
                high = mid - 1
            if value > interval_array[mid].left:
                low = mid + 1
        print("Error!")
        return None


class CDFGenerator(object):
    def __init__(self, cdf_distribution_file_path, pdf=None):
        self.source = "from_file"
        self.size_array = CDFGenerator.get_size_array(cdf_distribution_file_path)
        if not pdf:
            self.pdf = CDFGenerator.calculate_pdf_of_packets_from_cdf_file(cdf_distribution_file_path)
        else:
            self.pdf = pdf

    def get_sample(self):
        return np.random.choice(self.size_array, 1, p=self.pdf)[0]  # weighted choice

    # Pr(X > a) = P => f(p) = a
    def get_size_by_probability(self, p):
        cdf = 0
        for i in range(len(self.pdf)):
            cdf += self.pdf[i]
            if cdf >= p:
                return self.size_array[i]

    @staticmethod
    def calculate_pdf_of_packets_from_cdf_file(cdf_distribution_file_path):
        df = pd.read_csv(cdf_distribution_file_path, header=[0])
        size_header, cdf_header = df.columns
        pdf_value = []
        prev_cdf = 0
        for cdf_value in df[cdf_header]:
            pdf_value.append(cdf_value - prev_cdf)
            prev_cdf = cdf_value
        return pdf_value

    @staticmethod
    def get_size_array(cdf_distribution_file_path):
        df = pd.read_csv(cdf_distribution_file_path, header=[0])
        size_header, cdf_header = df.columns
        return df[size_header]
