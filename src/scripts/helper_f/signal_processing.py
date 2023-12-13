"""
    This module implements the low pass filter using Butterworth filtering
    Butterworth Filter:
    Imagine Cleaning Up a Noisy Sound:
    You're listening to your favorite song, but there's some annoying background noise. You want to clean it up and hear only the music.
    
    Butterworth Filter is Like a Music Cleaning Tool:
    The Butterworth filter is like a tool that helps clean up the sound. 
    It lets you choose which parts of the sound you want to keep (the music) and which parts you want to get rid of (the noise).
    
    Different Filters for Different Jobs:
    There are many types of filters, like different tools for different tasks. 
    The Butterworth filter is good for some jobs because it's smooth and doesn't cause a "bump" in the music you want to keep.
    
    How It Works:
    The Butterworth filter is designed to be good at letting through some frequencies (the music you want) and blocking others (the noise you want to remove).
    
    Order of the Filter:
    The "order" of the Butterworth filter is like the strength of the cleaning tool. 
    Higher order means it can do a better job, but sometimes you don't need it to be too strong.
    
    Smooth and Even:
    One special thing about the Butterworth filter is that it's smooth and even. 
    It doesn't create strange changes in the music as it cleans up the noise.
    
    In summary, a Butterworth filter is a tool that helps clean up signals, like music, by letting through the parts you want and blocking the parts you don't want. 
    It's chosen based on its ability to do this task smoothly and without causing distortion in the signal.

"""
from scipy.signal import butter, filtfilt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

class low_pass_filter:
    
    def __init__(self,
                signal,
                order,
                fs,
                cuttof_freq,
                time,
                filter_type='low',
                analog=False,
                output='ba'):
        
        self.signal = signal
        self.Nf = fs * 0.5
        self.Wn = cutoff_freq / self.Nf
        self.filter_type = filter_type
        self.ouput = output
        
        
    def fit(self):
        """
        Here, scipy.signal.butter function (Butterworth filter) is used to generate a filter.

        N: The order of the filter.
        
        Wn: The cutoff frequency or frequencies. 
        For a low-pass/high-pass filter, Wn is the normalized cutoff frequency. 
        Its value should be between 0 and 1, where 1 corresponds to half the sampling frequency (Nyquist frequency).
        For a band-pass or band-stop filter, Wn is a tuple (Wn1, Wn2) representing the lower and upper normalized cutoff frequencies.
        In simple terms, Wn sets the frequency at which the filter starts to have an effect, and its exact interpretation depends on the type of filter you are designing.

        btype: Filter type. It could be 'low' for low-pass, 'high' for high-pass, 'band' for band-pass, or 'stop' for band-stop.
        
        analog: If True, the filter is designed for analog (continuous-time) signal processing. If False (default), it's for digital signal processing.
        
        output: Type of output. 'ba' (default) returns numerator (b) and denominator (a) polynomials, 'zpk' returns zeros, poles, and gain, and 'sos' returns second-order sections.
        
        fs: The sampling frequency of the digital system. It's required if analog is False.
        """
        self.b, self.a = butter(N = self.order, 
                      Wn = self.Wn, 
                      btype=self.filter_type, 
                      analog=False, 
                      output=self.output, 
                      fs=None)
    
    def transform(self):
        """
            Apply the filter to the signal
        """
        filtered_signal = filtfilt(self.b, self.a, self.signal)
        return filtered_signal

class pca:
    def __init__(self,
                 df,
                 cols,
                 num_componenets):
        self.x = df[cols]
        self.n = num_components
    
    def fit(self):
        # Standardizing the features
        self.x = StandardScaler().fit_transform(self.x)
        
        # Perform PCA
        pca = PCA(num_cmponenets=self.n)
        
        principle_componenets = pca.fit_transform(self.x)
        
        self.pc_df = pd.DataFrame(principle_components,
                                  columns = [f"pc_{i}" for i in range(self.n)])
    