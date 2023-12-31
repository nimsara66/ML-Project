# -*- coding: utf-8 -*-
"""Speech-based_Classification_Layer-9_Label-4

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1QCkBQQ729ERL4Gs1SQUbORfcipCvr1qU

# Library Imports
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import VarianceThreshold
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score

"""# Import Datasets"""

train_csv_url = "/content/drive/MyDrive/#Semester07/CS4622/ML Project/speech-based-classification-layer-9/train.csv"
valid_csv_url = "/content/drive/MyDrive/#Semester07/CS4622/ML Project/speech-based-classification-layer-9/valid.csv"
test_csv_url = "/content/drive/MyDrive/#Semester07/CS4622/ML Project/speech-based-classification-layer-9/test.csv"

train_data = pd.read_csv(train_csv_url)
valid_data = pd.read_csv(valid_csv_url)
test_data = pd.read_csv(test_csv_url)

print("Train data:")
print(train_data.head())
print("Valid data:")
print(valid_data.head())
print("Test data:")
print(test_data.head())

"""# Data Visualization"""

def visualize_label(y, title, x_title, y_title='Number of entries'):
  unique_classes, class_counts = np.unique(y, return_counts=True)
  plt.bar(unique_classes, class_counts)
  plt.xlabel(x_title)
  plt.ylabel(y_title)
  plt.title(title)
  plt.show()

visualize_label(train_data['label_4'], "Number of rows versus Age","Age")

visualize_label(valid_data['label_4'], "Number of rows versus Age","Age")

"""# Outlier Detection and Removal"""

from scipy.stats import norm

def visualize_label_norm(y, title, x_title, y_title='Number of entries'):
  unique_classes, class_counts = np.unique(y, return_counts=True)
  plt.bar(unique_classes, class_counts)
  plt.xlabel(x_title)
  plt.ylabel(y_title)
  plt.title(title)

  rng = np.arange(train_data["label_4"].min(), train_data["label_4"].max(), 0.1)
  plt.plot(rng, norm.pdf(rng,train_data["label_4"].mean(),train_data["label_4"].std()))
  plt.show()

visualize_label_norm(train_data['label_4'], "Number of rows versus Age","Age")

train_data['zscore'] = ( train_data["label_4"] - train_data["label_4"].mean() ) / train_data["label_4"].std()
outliers = train_data[(train_data.zscore<-3) | (train_data.zscore>3)]
outliers.shape

"""No outliers to remove

# Train without Feaure Reduction
"""

print(f"train_data dataset shape {train_data.shape}")
print(f"# of missing values {train_data['label_4'].isna().sum()}")
print(f"# of labels {train_data['label_4'].value_counts().shape[0]}")
print(f"label summary\n{train_data['label_4'].value_counts()}")

train_data.dropna(subset=['label_4'], inplace=True)
print(f"train_data dataset shape {train_data.shape}")

"""Feature Enginering

*   Label_4 has no missing values
*   Label_4 has 14 unique classes
*   Using one-hot encoding for multilabel classification


"""

label_4 = train_data['label_4'].values.reshape(-1, 1)
ohe = OneHotEncoder(handle_unknown='ignore', sparse_output=False).fit(label_4)
print(ohe.categories_)

label_4 = ohe.transform(label_4)
print(label_4)

X_train, X_test, y_train, y_test = train_test_split(train_data.iloc[:, :768], label_4, test_size=0.2, stratify=label_4, random_state=2023)

X_train_tensors = torch.tensor(X_train.iloc[:, :].values, dtype=torch.float32)
print(X_train_tensors.shape)

X_test_tensors = torch.tensor(X_test.iloc[:, :].values, dtype=torch.float32)
print(X_test_tensors.shape)

"""## Define the Model"""

class AccentClassifier(nn.Module):
    def __init__(self, dropout_prob=0.5, weight_decay=1e-5):
        super(AccentClassifier, self).__init__()
        self.linear1 = nn.Linear(768, 512)
        self.linear2 = nn.Linear(512, 256)
        self.linear3 = nn.Linear(256, 128)
        self.linear4 = nn.Linear(128, 14)

        # Set weight_decay for regularization
        self.weight_decay = weight_decay

    def forward(self, tensors):
        output_l1 = torch.relu(self.linear1(tensors))
        output_l2 = torch.relu(self.linear2(output_l1))
        output_l3 = torch.relu(self.linear3(output_l2))
        output_l4 = self.linear4(output_l3)
        return output_l4

    def l2_regularization_loss(self):
        # Calculate L2 regularization loss for linear layers
        l2_loss = 0.0
        for param in self.parameters():
            if param.requires_grad:
                l2_loss += torch.norm(param, 2)
        return self.weight_decay * l2_loss

"""## Train the model"""

# Create an instance of the AccentClassifier model
accentClassifier = AccentClassifier()

# Define a cross-entropy loss function
criterion = nn.CrossEntropyLoss()

# Create a DataLoader for batching
batch_size = 128
dataset = TensorDataset(X_train_tensors, torch.tensor(y_train))
dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

# Define an optimizer
optimizer = torch.optim.Adam(accentClassifier.parameters(), lr=0.001)

# Define early stopping parameters
patience = 25
best_validation_accuracy = 0
no_improvement_counter = 0

# Training loop
epochs = 1000
for epoch in range(epochs):

    for inputs, targets in dataloader:
        optimizer.zero_grad()
        outputs = accentClassifier(inputs)

        ce_loss = criterion(outputs, targets)
        l2_loss = accentClassifier.l2_regularization_loss()

        total_loss = ce_loss + l2_loss

        total_loss.backward()
        optimizer.step()

    # Validation step (evaluate on validation dataset)
    with torch.no_grad():
        accentClassifier.eval()
        y_test_pred = accentClassifier(X_test_tensors)
        ce = criterion(y_test_pred, torch.tensor(y_test))
        acc = (torch.argmax(y_test_pred, 1) == torch.argmax(torch.tensor(y_test), 1)).float().mean()
        accentClassifier.train()

    print(f"Epoch {epoch} validation: Cross-entropy={float(ce)}, Accuracy={float(acc)}")

    # Check for early stopping
    if acc > best_validation_accuracy:
        best_validation_accuracy = acc
        no_improvement_counter = 0
        # Save the trained best model if needed
        torch.save(accentClassifier.state_dict(), 'accentClassifier_model.pth')
    else:
        no_improvement_counter += 1

    # If no improvement for 'patience' consecutive epochs, stop training
    if no_improvement_counter >= patience:
        print("Early stopping triggered. Training stopped.")
        break

# Create an instance of the model
accentClassifier = AccentClassifier()

# Load the saved model state dictionary
accentClassifier.load_state_dict(torch.load('/content/drive/Shareddrives/test/ML _Project/accentClassifier_model.pth'))

# Validation step (evaluate on validation dataset)
with torch.no_grad():
    accentClassifier.eval()
    y_test_pred = accentClassifier(X_test_tensors)
    ce = criterion(y_test_pred, torch.tensor(y_test))
    acc = (torch.argmax(y_test_pred, 1) == torch.argmax(torch.tensor(y_test), 1)).float().mean()

print(f"Best model validation: Cross-entropy={float(ce)}, Accuracy={float(acc)}")

"""## Evaluation of the Model"""

valid_data.dropna(subset=['label_4'], inplace=True)
print(f"valid_data dataset shape {valid_data.shape}")

label_4_eval = valid_data['label_4'].values.reshape(-1, 1)
ohe = OneHotEncoder(handle_unknown='ignore', sparse_output=False).fit(label_4_eval)
print(ohe.categories_)

label_4_eval = ohe.transform(label_4_eval)
print(label_4_eval)

# Set your model to evaluation mode
accentClassifier.eval()

X_valid_tensors = torch.tensor(valid_data.iloc[:, :768].values, dtype=torch.float32)
print(X_valid_tensors.shape)

y_pred = accentClassifier(X_valid_tensors)
ce = criterion(y_pred, torch.tensor(label_4_eval))
acc = (torch.argmax(y_pred, 1) == torch.argmax(torch.tensor(label_4_eval), 1)).float().mean()
print(f"Cross-entropy={float(ce)}, Test Accuracy={float(acc)}")

valid_data_c = valid_data.copy()

y_pred_one_hot = ohe.inverse_transform(y_pred.detach().numpy())
valid_data_c["label_4_pred"] = pd.DataFrame(y_pred_one_hot, columns=["label_4_pred"])

valid_data_c.iloc[:, 771:].head(100)

y_pred_labels = torch.argmax(y_pred, axis=1).numpy()
label_4_np = torch.argmax(torch.tensor(label_4_eval), axis=1).numpy()

confusion = confusion_matrix(label_4_np, y_pred_labels)
print(classification_report(label_4_np, y_pred_labels))

accuracy_score(label_4_np, y_pred_labels)

"""## Fixing class imbalance"""

from imblearn.over_sampling import SMOTE

# transform the dataset
oversample = SMOTE()
X_train_balanced, y_train_balanced = oversample.fit_resample(X_train, y_train)

print(X_train_balanced.shape)
print(y_train_balanced.shape)

y_train_balanced

# Create an instance of the AccentClassifier model
accentClassifierOverSample = AccentClassifier()

# Define a cross-entropy loss function
criterion = nn.CrossEntropyLoss()

# Create a DataLoader for batching
batch_size = 128
dataset = TensorDataset(torch.tensor(X_train_balanced.values, dtype=torch.float32), torch.tensor(y_train_balanced))
dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

# Define an optimizer
optimizer = torch.optim.Adam(accentClassifierOverSample.parameters(), lr=0.001)

# Define early stopping parameters
patience = 25
best_validation_accuracy = 0
no_improvement_counter = 0

# Training loop
epochs = 1000
for epoch in range(epochs):

    for inputs, targets in dataloader:
        optimizer.zero_grad()
        outputs = accentClassifierOverSample(inputs)
        ce_loss = criterion(outputs, targets.float())
        l2_loss = accentClassifierOverSample.l2_regularization_loss()

        total_loss = ce_loss + l2_loss

        total_loss.backward()
        optimizer.step()

    # Validation step (evaluate on validation dataset)
    with torch.no_grad():
        accentClassifierOverSample.eval()
        y_test_pred = accentClassifierOverSample(X_test_tensors)
        ce = criterion(y_test_pred, torch.tensor(y_test))
        acc = (torch.argmax(y_test_pred, 1) == torch.argmax(torch.tensor(y_test), 1)).float().mean()
        accentClassifierOverSample.train()

    print(f"Epoch {epoch} validation: Cross-entropy={float(ce)}, Accuracy={float(acc)}")

    # Check for early stopping
    if acc > best_validation_accuracy:
        best_validation_accuracy = acc
        no_improvement_counter = 0
        # Save the trained best model if needed
        torch.save(accentClassifierOverSample.state_dict(), 'accentClassifierOverSample_model.pth')
    else:
        no_improvement_counter += 1

    # If no improvement for 'patience' consecutive epochs, stop training
    if no_improvement_counter >= patience:
        print("Early stopping triggered. Training stopped.")
        break

# Create an instance of the model
accentClassifierOverSample = AccentClassifier()

# Load the saved model state dictionary
accentClassifierOverSample.load_state_dict(torch.load('/content/drive/Shareddrives/test/ML _Project/accentClassifierOverSample_model.pth'))

# Validation step (evaluate on validation dataset)
with torch.no_grad():
    accentClassifierOverSample.eval()
    y_test_pred = accentClassifierOverSample(X_test_tensors)
    ce = criterion(y_test_pred, torch.tensor(y_test))
    acc = (torch.argmax(y_test_pred, 1) == torch.argmax(torch.tensor(y_test), 1)).float().mean()

print(f"Best model validation: Cross-entropy={float(ce)}, Accuracy={float(acc)}")

"""We get better results without oversampling

## Get Test Results
"""

# Set your model to evaluation mode
accentClassifier.eval()

X_t_tensors = torch.tensor(test_data.iloc[:, :768].values, dtype=torch.float32)
print(X_t_tensors.shape)

y_pred_t = accentClassifier(X_t_tensors)
print(y_pred_t.shape)

y_pred_one_hot = ohe.inverse_transform(y_pred_t.detach().numpy())
test_data["label_4"] = pd.DataFrame(y_pred_one_hot, columns=["label_4"])

test_data.head()

file_path = "/content/drive/MyDrive/#Semester07/CS4622/ML Project/speech-based-classification-layer-9/label_4.csv"

# Save the DataFrame to a CSV file
test_data.to_csv(file_path, index=False)

"""# Train with Feature Engineering"""

data_features = train_data.iloc[:, :768]

"""## Drop Constant Features Using Variance Threshold"""

var_thres=VarianceThreshold(threshold=0)
var_thres.fit(data_features)

constant_columns = [column for column in data_features.columns
                    if column not in data_features.columns[var_thres.get_support()]]

print(constant_columns)

"""There is no constant columns

## Drop Features Using Pearson Correlation
"""

data_features.corr()

# Using Pearson Correlation
plt.figure(figsize=(12,10))
cor = data_features.corr()
sns.heatmap(cor, annot=True, cmap=plt.cm.CMRmap_r)
plt.show()

def correlation(dataset, threshold):
    correlated_pairs = set()
    corr_matrix = dataset.corr()
    for i in range(len(corr_matrix.columns)):
        for j in range(i):
            if abs(corr_matrix.iloc[i, j]) > threshold: # we are interested in absolute coeff value
                colname = corr_matrix.columns[i]  # getting the name of column
                rowname = corr_matrix.index[j]  # getting the name of row
                correlated_pairs.add((rowname, colname))
    return correlated_pairs

def get_less_correlated_features(correlated_pairs, dataset, target_column):
    less_correlated_features = {}

    for (feature1, feature2) in correlated_pairs:
        corr1 = dataset[feature1].corr(dataset[target_column])
        corr2 = dataset[feature2].corr(dataset[target_column])

        if abs(corr1) < abs(corr2):
            correlated_pair = frozenset((feature1, feature2))  # Use a frozenset as the key
            less_correlated_features[correlated_pair] = feature1
        else:
            correlated_pair = frozenset((feature1, feature2))  # Use a frozenset as the key
            less_correlated_features[correlated_pair] = feature2

    return less_correlated_features

corr_feature_pairs = correlation(data_features, 0.9)
corr_feature_pairs

less_correlated_features = get_less_correlated_features(corr_feature_pairs, train_data, "label_4")
less_correlated_features

corr_features = set(less_correlated_features.values())
corr_features

new_features = data_features.drop(corr_features,axis=1)

print(data_features.shape)
print(new_features.shape)

"""## Train the model"""

class AccentClassifierAfter(nn.Module):
    def __init__(self, dropout_prob=0.5, weight_decay=1e-5):
        super(AccentClassifierAfter, self).__init__()
        self.linear1 = nn.Linear(767, 512)
        self.linear2 = nn.Linear(512, 256)
        self.linear3 = nn.Linear(256, 128)
        self.linear4 = nn.Linear(128, 14)

        # Set weight_decay for regularization
        self.weight_decay = weight_decay

    def forward(self, tensors):
        output_l1 = torch.relu(self.linear1(tensors))
        output_l2 = torch.relu(self.linear2(output_l1))
        output_l3 = torch.relu(self.linear3(output_l2))
        output_l4 = self.linear4(output_l3)
        return output_l4

    def l2_regularization_loss(self):
        # Calculate L2 regularization loss for linear layers
        l2_loss = 0.0
        for param in self.parameters():
            if param.requires_grad:
                l2_loss += torch.norm(param, 2)
        return self.weight_decay * l2_loss

label_4 = train_data['label_4'].values.reshape(-1, 1)
ohe = OneHotEncoder(handle_unknown='ignore', sparse_output=False).fit(label_4)
print(ohe.categories_)

label_4 = ohe.transform(label_4)
print(label_4)

X_train_after, X_test_after, y_train_after, y_test_after = train_test_split(new_features, label_4, test_size=0.2, stratify=label_4, random_state=2023)

X_train_tensors_after = torch.tensor(X_train_after.values, dtype=torch.float32)
print(X_train_tensors_after.shape)


X_test_tensors_after = torch.tensor(X_test_after.values, dtype=torch.float32)
print(X_test_tensors_after.shape)

y_train_after.shape

# Create an instance of the AccentClassifierAfter model
accentClassifierAfter = AccentClassifierAfter()

# Define a cross-entropy loss function
criterion = nn.CrossEntropyLoss()

# Create a DataLoader for batching
batch_size = 128
dataset = TensorDataset(X_train_tensors_after, torch.tensor(y_train_after))
dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

# Define an optimizer
optimizer = torch.optim.Adam(accentClassifierAfter.parameters(), lr=0.001)

# Define early stopping parameters
patience = 25
best_validation_accuracy = 0
no_improvement_counter = 0

# Training loop
epochs = 1000
for epoch in range(epochs):

    for inputs, targets in dataloader:
        optimizer.zero_grad()
        outputs = accentClassifierAfter(inputs)

        ce_loss = criterion(outputs, targets)
        l2_loss = accentClassifierAfter.l2_regularization_loss()

        total_loss = ce_loss + l2_loss

        total_loss.backward()
        optimizer.step()

    # Validation step (evaluate on validation dataset)
    with torch.no_grad():
        accentClassifierAfter.eval()
        y_test_pred_after = accentClassifierAfter(X_test_tensors_after)
        ce = criterion(y_test_pred_after, torch.tensor(y_test_after))
        acc = (torch.argmax(y_test_pred_after, 1) == torch.argmax(torch.tensor(y_test_after), 1)).float().mean()
        accentClassifierAfter.train()

    print(f"Epoch {epoch} validation: Cross-entropy={float(ce)}, Accuracy={float(acc)}")

    # Check for early stopping
    if acc > best_validation_accuracy:
        best_validation_accuracy = acc
        no_improvement_counter = 0
        # Save the trained best model if needed
        torch.save(accentClassifierAfter.state_dict(), 'accentClassifierAfter_model.pth')
    else:
        no_improvement_counter += 1

    # If no improvement for 'patience' consecutive epochs, stop training
    if no_improvement_counter >= patience:
        print("Early stopping triggered. Training stopped.")
        break

# Create an instance of the model
accentClassifierAfter = AccentClassifierAfter()

# Define a cross-entropy loss function
criterion = nn.CrossEntropyLoss()

# Load the saved model state dictionary
accentClassifierAfter.load_state_dict(torch.load('/content/drive/Shareddrives/test/ML _Project/accentClassifierAfter_model.pth'))

# Validation step (evaluate on validation dataset)
with torch.no_grad():
    accentClassifierAfter.eval()
    y_test_pred_after = accentClassifierAfter(X_test_tensors_after)
    ce = criterion(y_test_pred_after, torch.tensor(y_test_after))
    acc = (torch.argmax(y_test_pred_after, 1) == torch.argmax(torch.tensor(y_test_after), 1)).float().mean()

print(f"Best model validation: Cross-entropy={float(ce)}, Accuracy={float(acc)}")

"""## Evaluation of the Model"""

# Set your model to evaluation mode
accentClassifierAfter.eval()

new_features_valid = valid_data.iloc[:, :768].drop(corr_features,axis=1)
X_valid_tensors_after = torch.tensor(new_features_valid.values, dtype=torch.float32)
print(X_valid_tensors_after.shape)

y_pred_valid_after = accentClassifierAfter(X_valid_tensors_after)
ce = criterion(y_pred_valid_after, torch.tensor(label_4_eval))
acc = (torch.argmax(y_pred_valid_after, 1) == torch.argmax(torch.tensor(label_4_eval), 1)).float().mean()
print(f"Cross-entropy={float(ce)}, Test Accuracy={float(acc)}")

y_pred_valid_after_labels = torch.argmax(y_pred_valid_after, axis=1).numpy()
label_4_np_valid_after = torch.argmax(torch.tensor(label_4_eval), axis=1).numpy()

confusion = confusion_matrix(label_4_np_valid_after, y_pred_valid_after_labels)
print(classification_report(label_4_np_valid_after, y_pred_valid_after_labels))

accuracy_score(label_4_np_valid_after, y_pred_valid_after_labels)

"""## Get Test Results"""

# Set your model to evaluation mode
accentClassifierAfter.eval()

new_features_test = test_data.iloc[:, :768].drop(corr_features,axis=1)
X_t_tensors_after = torch.tensor(new_features_test.values, dtype=torch.float32)
print(X_t_tensors_after.shape)

y_pred_t_after = accentClassifierAfter(X_t_tensors_after)
print(y_pred_t_after.shape)

y_pred_one_hot = ohe.inverse_transform(y_pred_t_after.detach().numpy())
test_data["label_4"] = pd.DataFrame(y_pred_one_hot, columns=["label_4"])

test_data.head()

file_path = "/content/drive/MyDrive/#Semester07/CS4622/ML Project/speech-based-classification-layer-9/label_4.csv"

# Save the DataFrame to a CSV file
test_data.to_csv(file_path, index=False)