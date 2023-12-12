# -*- coding: utf-8 -*-
"""outlier_detection.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ht-_oGeOq_SzW1zOZ8auuuo4FzTfO8cO
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import scipy
from sklearn.neighbors import LocalOutlierFactor  # pip install scikit-learn

# --------------------------------------------------------------
# Load data
# --------------------------------------------------------------
df = pd.read_pickle("/content/01_data_processed.pkl")

display(df.head())

# --------------------------------------------------------------
# Plotting outliers
# --------------------------------------------------------------
plt.style.use("fivethirtyeight")
plt.rcParams["figure.figsize"] = (20, 5)
plt.rcParams["figure.dpi"] = 100

df[["acc_y", "excercise"]].plot(by = "excercise",
                                kind = "box",
                                figsize = (10, 5),
                                label = "excercise", )

df[["gyro_y", "excercise"]].plot(by = "excercise",
                                kind = "box",
                                figsize = (10, 5),
                                label = "excercise", )

col_num = list(df.select_dtypes([np.number]).columns)
col_num.remove("ind")
# Plotting accelerometer data
df[col_num[:3] + ["excercise"]].plot(by = "excercise",
                                kind = "box",
                                figsize = (30, 10),
                                label = "excercise",
                                     layout = (1, 3))

# Plotting gyroscope data
df[col_num[3:6] + ["excercise"]].plot(by = "excercise",
                                kind = "box",
                                figsize = (30, 10),
                                label = "excercise",
                                      layout = (1, 3))

# Plotting outliers in time
def plot_binary_outliers(dataset, col, outlier_col, reset_index):
    """ Plot outliers in case of a binary outlier score. Here, the col specifies the real data
    column and outlier_col the columns with a binary value (outlier or not).

    Args:
        dataset (pd.DataFrame): The dataset
        col (string): Column that you want to plot
        outlier_col (string): Outlier column marked with true/false
        reset_index (bool): whether to reset the index for plotting
    """

    # Taken from: https://github.com/mhoogen/ML4QS/blob/master/Python3Code/util/VisualizeDataset.py

    dataset = dataset.dropna(axis=0, subset=[col, outlier_col])
    dataset[outlier_col] = dataset[outlier_col].astype("bool")

    if reset_index:
        dataset = dataset.reset_index()

    fig, ax = plt.subplots()

    plt.xlabel("samples")
    plt.ylabel("value")

    # Plot non outliers in default color
    ax.plot(
        dataset.index[~dataset[outlier_col]],
        dataset[col][~dataset[outlier_col]],
        "+",
    )
    # Plot data points that are outliers in red
    ax.plot(
        dataset.index[dataset[outlier_col]],
        dataset[col][dataset[outlier_col]],
        "r+",
    )

    plt.legend(
        ["outlier " + col, "no outlier " + col],
        loc="upper center",
        ncol=2,
        fancybox=True,
        shadow=True,
    )
    plt.show()

# --------------------------------------------------------------
# Interquartile range (distribution based)
# --------------------------------------------------------------

# Insert IQR function
def mark_outliers_iqr(df, col):
  df = df.copy()
  Q1 = np.percentile(df[col], 25, method='midpoint')
  Q3 = np.percentile(df[col], 75, method='midpoint')
  IQR = Q3 - Q1
  df[f"{col}_outlier"] = np.array((df[col] > Q3 + IQR * 1.5) | (df[col] < Q1 - IQR * 1.5))
  return df

# Plot a single column
col = "gyro_z"
df_distribution = mark_outliers_iqr(df, col)
plot_binary_outliers(df_distribution, col, f"{col}_outlier", True)

# Loop over all columns
for col in col_num:
  df_distribution = outliers(df, col)
  # Plot a single column
  plot_binary_outliers(df_distribution, col, f"{col}_outlier", True)

# --------------------------------------------------------------
# Chauvenets criteron (distribution based)
# --------------------------------------------------------------

# Check for normal distribution
df[col_num[:3] + ["excercise"]].plot(by = "excercise",
                                kind = "hist",
                                figsize = (15, 15),
                                label = "excercise",
                                     layout = (3, 3))

df[col_num[3:6] + ["excercise"]].plot(by = "excercise",
                                kind = "hist",
                                figsize = (15, 15),
                                label = "excercise",
                                     layout = (3, 3))

# Insert Chauvenet's function
def mark_outliers_chauvenet(dataset, col, C=2):
    """Finds outliers in the specified column of datatable and adds a binary column with
    the same name extended with '_outlier' that expresses the result per data point.

    Taken from: https://github.com/mhoogen/ML4QS/blob/master/Python3Code/Chapter3/OutlierDetection.py

    Args:
        dataset (pd.DataFrame): The dataset
        col (string): The column you want apply outlier detection to
        C (int, optional): Degree of certainty for the identification of outliers given the assumption
                           of a normal distribution, typicaly between 1 - 10. Defaults to 2.

    Returns:
        pd.DataFrame: The original dataframe with an extra boolean column
        indicating whether the value is an outlier or not.
    """

    dataset = dataset.copy()
    # Compute the mean and standard deviation.
    mean = dataset[col].mean()
    std = dataset[col].std()
    N = len(dataset.index)
    criterion = 1.0 / (C * N)

    # Consider the deviation for the data points.
    deviation = abs(dataset[col] - mean) / std

    # Express the upper and lower bounds.
    low = -deviation / math.sqrt(C)
    high = deviation / math.sqrt(C)
    prob = []
    mask = []

    # Pass all rows in the dataset.
    for i in range(0, len(dataset.index)):
        # Determine the probability of observing the point
        prob.append(
            1.0 - 0.5 * (scipy.special.erf(high[i]) - scipy.special.erf(low[i]))
        )
        # And mark as an outlier when the probability is below our criterion.
        mask.append(prob[i] < criterion)
    dataset[col + "_outlier"] = mask
    return dataset

# Loop over all columns
for col in col_num:
  df_chauv = mark_outliers_chauvenet(df, col, C=2)
  # Plot a single column
  plot_binary_outliers(df_chauv, col, f"{col}_outlier", True)

# --------------------------------------------------------------
# Local outlier factor (distance based)
# --------------------------------------------------------------

# Insert LOF function
def mark_outliers_lof(dataset, columns, n=20):
    """Mark values as outliers using LOF

    Args:
        dataset (pd.DataFrame): The dataset
        col (string): The column you want apply outlier detection to
        n (int, optional): n_neighbors. Defaults to 20.

    Returns:
        pd.DataFrame: The original dataframe with an extra boolean column
        indicating whether the value is an outlier or not.
    """

    dataset = dataset.copy()

    lof = LocalOutlierFactor(n_neighbors=n)
    data = dataset[columns]
    outliers = lof.fit_predict(data)
    X_scores = lof.negative_outlier_factor_

    dataset["outlier_lof"] = outliers == -1
    return dataset, outliers, X_scores

# Loop over all columns
df_loc, outliers, X_scores = mark_outliers_lof(df, col_num, n=20)
# Plot a single column
for col in col_num:
  plot_binary_outliers(df_loc, col, "outlier_lof", True)

# --------------------------------------------------------------
# Check outliers grouped by label
# --------------------------------------------------------------
# Loop over all columns
label = "bench"
for col in col_num:
  df_iqr_label = mark_outliers_iqr(df[df["excercise"] == label], col)
  # Plot a single column
  plot_binary_outliers(df_iqr_label, col, f"{col}_outlier", True)

# Usign Chavenet
for col in col_num:
  df_chauv_label = mark_outliers_chauvenet(df[df["excercise"] == label], col)
  # Plot a single column
  plot_binary_outliers(df_chauv_label, col, f"{col}_outlier", True)

# Usign LOF function
df_loc_label, outliers, X_scores = mark_outliers_lof(df[df["excercise"] == label], col_num, n=20)
# Plot a single column
for col in col_num:
  plot_binary_outliers(df_loc_label, col, "outlier_lof", True)

# --------------------------------------------------------------
# Choose method and deal with outliers
# --------------------------------------------------------------
label = "gyro_y"
# Test on single column
dataset = mark_outliers_chauvenet(df, col = label)
dataset.loc[dataset[f"{label}_outlier"], label] = np.nan
dataset[dataset[f"{label}_outlier"]]

# Create a loop
dataset = df.copy()
for col in col_num:
  for label in df.excercise.unique():
    dataset_label = mark_outliers_chauvenet(dataset[dataset["excercise"] == label], col)

    # Set dataset_label values to np.nan
    dataset_label.loc[dataset_label[f"{col}_outlier"], col] = np.nan

    # Update the dataset
    dataset.loc[(dataset["excercise"] == label), col] = dataset_label[col]

# --------------------------------------------------------------
# Export new dataframe
# --------------------------------------------------------------
dataset.info()
dataset.to_pickle("02_data_outlier_removed.pkl")

df_1 = pd.read_pickle("/content/02_data_outlier_removed.pkl")

df_1.info()

