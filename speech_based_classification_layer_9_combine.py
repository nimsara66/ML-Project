# -*- coding: utf-8 -*-
"""Speech-based_Classification_Layer-9_Combine

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Qy1JfG7GVyZv8eJryqiJsxx0lbpYHV-h

# Library Imports
"""

import pandas as pd

"""# Import Datasets"""

label_1_csv_url = "/content/drive/MyDrive/#Semester07/CS4622/ML Project/speech-based-classification-layer-9/label_1.csv"
label_2_csv_url = "/content/drive/MyDrive/#Semester07/CS4622/ML Project/speech-based-classification-layer-9/label_2.csv"
label_3_csv_url = "/content/drive/MyDrive/#Semester07/CS4622/ML Project/speech-based-classification-layer-9/label_3.csv"
label_4_csv_url = "/content/drive/MyDrive/#Semester07/CS4622/ML Project/speech-based-classification-layer-9/label_4.csv"

label_1_data = pd.read_csv(label_1_csv_url)
label_2_data = pd.read_csv(label_2_csv_url)
label_3_data = pd.read_csv(label_3_csv_url)
label_4_data = pd.read_csv(label_4_csv_url)

label_1_data.head()

Classification_Layer_9 = label_1_data[["ID", "label_1"]].copy()

Classification_Layer_9["label_2"] = label_2_data["label_2"]
Classification_Layer_9["label_3"] = label_3_data["label_3"]
Classification_Layer_9["label_4"] = label_4_data["label_4"]

Classification_Layer_9.head()

file_path = "/content/drive/MyDrive/#Semester07/CS4622/ML Project/speech-based-classification-layer-9/Classification_Layer_9.csv"

# Save the DataFrame to a CSV file
Classification_Layer_9.to_csv(file_path, index=False)