# -*- coding: utf-8 -*-
"""build_features.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/180sR4eP6NOSP5L2SGioKarkAEgbyDERU
"""

##############################################################
#                                                            #
#    Mark Hoogendoorn and Burkhardt Funk (2017)              #
#    Machine Learning for the Quantified Self                #
#    Springer                                                #
#    Chapter 3                                               #
#                                                            #
##############################################################

# Updated by Dave Ebbelaar on 22-12-2022

from sklearn.decomposition import PCA
from scipy.signal import butter, lfilter, filtfilt
import copy
import pandas as pd

# This class removes the high frequency data (that might be considered noise) from the data.
# We can only apply this when we do not have missing values (i.e. NaN).
class LowPassFilter:
    def low_pass_filter(
        self,
        data_table,
        col,
        sampling_frequency,
        cutoff_frequency,
        order=5,
        phase_shift=True,
    ):
        # http://stackoverflow.com/questions/12093594/how-to-implement-band-pass-butterworth-filter-with-scipy-signal-butter
        # Cutoff frequencies are expressed as the fraction of the Nyquist frequency, which is half the sampling frequency
        nyq = 0.5 * sampling_frequency
        cut = cutoff_frequency / nyq

        b, a = butter(order, cut, btype="low", output="ba", analog=False)
        if phase_shift:
            data_table[col + "_lowpass"] = filtfilt(b, a, data_table[col])
        else:
            data_table[col + "_lowpass"] = lfilter(b, a, data_table[col])
        return data_table


# Class for Principal Component Analysis. We can only apply this when we do not have missing values (i.e. NaN).
# For this we have to impute these first, be aware of this.
class PrincipalComponentAnalysis:

    pca = []

    def __init__(self):
        self.pca = []

    def normalize_dataset(self, data_table, columns):
        dt_norm = copy.deepcopy(data_table)
        for col in columns:
            dt_norm[col] = (data_table[col] - data_table[col].mean()) / (
                data_table[col].max()
                - data_table[col].min()
                # data_table[col].std()
            )
        return dt_norm

    # Perform the PCA on the selected columns and return the explained variance.
    def determine_pc_explained_variance(self, data_table, cols):

        # Normalize the data first.
        dt_norm = self.normalize_dataset(data_table, cols)

        # perform the PCA.
        self.pca = PCA(n_components=len(cols))
        self.pca.fit(dt_norm[cols])
        # And return the explained variances.
        return self.pca.explained_variance_ratio_

    # Apply a PCA given the number of components we have selected.
    # We add new pca columns.
    def apply_pca(self, data_table, cols, number_comp):

        # Normalize the data first.
        dt_norm = self.normalize_dataset(data_table, cols)

        # perform the PCA.
        self.pca = PCA(n_components=number_comp)
        self.pca.fit(dt_norm[cols])

        # Transform our old values.
        new_values = self.pca.transform(dt_norm[cols])

        # And add the new ones:
        for comp in range(0, number_comp):
            data_table["pca_" + str(comp + 1)] = new_values[:, comp]

        return data_table

##############################################################
#                                                            #
#    Mark Hoogendoorn and Burkhardt Funk (2017)              #
#    Machine Learning for the Quantified Self                #
#    Springer                                                #
#    Chapter 4                                               #
#                                                            #
##############################################################

# Updated by Dave Ebbelaar on 22-12-2022

import numpy as np
import scipy.stats as stats

# Class to abstract a history of numerical values we can use as an attribute.
class NumericalAbstraction:

    # This function aggregates a list of values using the specified aggregation
    # function (which can be 'mean', 'max', 'min', 'median', 'std')
    def aggregate_value(self, aggregation_function):
        # Compute the values and return the result.
        if aggregation_function == "mean":
            return np.mean
        elif aggregation_function == "max":
            return np.max
        elif aggregation_function == "min":
            return np.min
        elif aggregation_function == "median":
            return np.median
        elif aggregation_function == "std":
            return np.std
        else:
            return np.nan

    # Abstract numerical columns specified given a window size (i.e. the number of time points from
    # the past considered) and an aggregation function.
    def abstract_numerical(self, data_table, cols, window_size, aggregation_function):

        # Create new columns for the temporal data, pass over the dataset and compute values
        for col in cols:
            data_table[
                col + "_temp_" + aggregation_function + "_ws_" + str(window_size)
            ] = (
                data_table[col]
                .rolling(window_size)
                .apply(self.aggregate_value(aggregation_function))
            )

        return data_table

##############################################################
#                                                            #
#    Mark Hoogendoorn and Burkhardt Funk (2017)              #
#    Machine Learning for the Quantified Self                #
#    Springer                                                #
#    Chapter 4                                               #
#                                                            #
##############################################################

# Updated by Dave Ebbelaar on 06-01-2023

import numpy as np


# This class performs a Fourier transformation on the data to find frequencies that occur
# often and filter noise.
class FourierTransformation:

    # Find the amplitudes of the different frequencies using a fast fourier transformation. Here,
    # the sampling rate expresses the number of samples per second (i.e. Frequency is Hertz of the dataset).
    def find_fft_transformation(self, data, sampling_rate):
        # Create the transformation, this includes the amplitudes of both the real
        # and imaginary part.
        transformation = np.fft.rfft(data, len(data))
        return transformation.real, transformation.imag

    # Get frequencies over a certain window.
    def abstract_frequency(self, data_table, cols, window_size, sampling_rate):

        # Create new columns for the frequency data.
        freqs = np.round((np.fft.rfftfreq(int(window_size)) * sampling_rate), 3)

        for col in cols:
            data_table[col + "_max_freq"] = np.nan
            data_table[col + "_freq_weighted"] = np.nan
            data_table[col + "_pse"] = np.nan
            for freq in freqs:
                data_table[
                    col + "_freq_" + str(freq) + "_Hz_ws_" + str(window_size)
                ] = np.nan

        # Pass over the dataset (we cannot compute it when we do not have enough history)
        # and compute the values.
        for i in range(window_size, len(data_table.index)):
            for col in cols:
                real_ampl, imag_ampl = self.find_fft_transformation(
                    data_table[col].iloc[
                        i - window_size : min(i + 1, len(data_table.index))
                    ],
                    sampling_rate,
                )
                # We only look at the real part in this implementation.
                for j in range(0, len(freqs)):
                    data_table.loc[
                        i, col + "_freq_" + str(freqs[j]) + "_Hz_ws_" + str(window_size)
                    ] = real_ampl[j]
                # And select the dominant frequency. We only consider the positive frequencies for now.

                data_table.loc[i, col + "_max_freq"] = freqs[
                    np.argmax(real_ampl[0 : len(real_ampl)])
                ]
                data_table.loc[i, col + "_freq_weighted"] = float(
                    np.sum(freqs * real_ampl)
                ) / np.sum(real_ampl)
                PSD = np.divide(np.square(real_ampl), float(len(real_ampl)))
                PSD_pdf = np.divide(PSD, np.sum(PSD))
                data_table.loc[i, col + "_pse"] = -np.sum(np.log(PSD_pdf) * PSD_pdf)

        return data_table

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --------------------------------------------------------------
# Load data
# --------------------------------------------------------------
df = pd.read_pickle("/content/02_data_outlier_removed.pkl")
predictor_columns = df.columns[:6]
# Plot settings
plt.style.use("fivethirtyeight")
100
plt.rcParams["lines.linewidth"] = 2
plt.rcParams["figure.figsize"] = (20, 5)
plt.rcParams["figure.dpi"]

# --------------------------------------------------------------
# Dealing with missing values (imputation)
# --------------------------------------------------------------
for col in predictor_columns:
  df[col] = df[col].interpolate()

df.info()

# --------------------------------------------------------------
# Calculating ind duration
# --------------------------------------------------------------
for set_ind in np.sort(df["ind"].unique()):
  duration = df[df["ind"] == set_ind].index[-1] - df[df["ind"] == set_ind].index[0]
  print(f"Set {set_ind} duration is {duration.seconds}")
  df.loc[(df["ind"] == set_ind), "duration"] = duration.seconds

df["intensity"] = df["intensity"].replace(regex={r'^heavy.*': 'heavy', r'^medium.*': 'medium'})

dataset = df.groupby("intensity").duration.mean()
print(dataset[0] / 5)
print(dataset[1] / 10)

# --------------------------------------------------------------
# Butterworth lowpass filter
# --------------------------------------------------------------
df_lowpass = df.copy()
low_pass = LowPassFilter()

df_lowpass = low_pass.low_pass_filter(df_lowpass,
        "acc_y",
        sampling_frequency = 1/0.2,
        cutoff_frequency = 1.3,
        order=5,
        phase_shift=True)

df_lowpass[df_lowpass["excercise"] == "dead"]

subset = df_lowpass[df_lowpass["ind"] == 54]
print(subset ["excercise"][0])
fig, ax = plt.subplots(nrows=2, sharex=True, figsize=(20, 10))
ax[0].plot(subset ["acc_y"].reset_index (drop=True), label="raw data")
ax[1].plot(subset ["acc_y_lowpass"].reset_index(drop=True), label="butterworth filter")
ax[0].legend (loc="upper center", bbox_to_anchor=(0.5, 1.15), fancybox=True, shadow=True)
ax [1]. legend (loc="upper center", bbox_to_anchor=(0.5, 1.15), fancybox=True, shadow=True)

# Loop to add on all columns
df_lowpass = df.copy()
for col in predictor_columns:
  low_pass = LowPassFilter()
  df_lowpass = low_pass.low_pass_filter(df_lowpass,
        col,
        sampling_frequency = 1/0.2,
        cutoff_frequency = 1.3,
        order=5,
        phase_shift=True)
df_lowpass.head()

# --------------------------------------------------------------
# Principal component analysis PCA
# --------------------------------------------------------------
pca_new = PrincipalComponentAnalysis()
df_pca = df_lowpass.copy()

pc_values = pca_new.determine_pc_explained_variance(df_pca, predictor_columns)

plt.figure(figsize=(10, 10))
plt.plot(range(1, len (predictor_columns) + 1), pc_values)
plt.xlabel("principal component number")
plt.ylabel("explained variance")
plt.show()

df_pca = pca_new.apply_pca(df_pca, predictor_columns, 3)

df_pca.head()

df_pca[df_pca["ind"] == 40].iloc[:, -3:].reset_index(drop= True).plot()

# --------------------------------------------------------------
# Sum of squares attributes
# --------------------------------------------------------------
df_pca["acc_sum"] = np.sqrt(np.sum(df_pca[["acc_x", "acc_y", "acc_z"]] ** 2, axis = 1))
df_pca["gyro_sum"] = np.sqrt(np.sum(df_pca[["gyro_x", "gyro_y", "gyro_z"]] ** 2, axis = 1))

df_pca[df_pca["ind"] == 84].iloc[:, -2:].reset_index(drop= True).plot(subplots = True)

df_pca.head()

# --------------------------------------------------------------
# Temporal abstraction
# --------------------------------------------------------------

# --------------------------------------------------------------
# Frequency features
# --------------------------------------------------------------

# --------------------------------------------------------------
# Dealing with overlapping windows
# --------------------------------------------------------------

# --------------------------------------------------------------
# Clustering
# --------------------------------------------------------------

# --------------------------------------------------------------
# Export dataset
# --------------------------------------------------------------