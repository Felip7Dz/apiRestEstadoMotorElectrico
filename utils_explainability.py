import numpy as np
import pandas as pd
from scipy.signal import filtfilt, butter
from scipy.stats import kurtosis, skew
import enter_utils


def computeRMS(data):
    return np.sqrt(np.mean(np.square(data)))


def computeSkewness(data):
    return skew(data)


def computeKurtosis(data):
    return kurtosis(data)


def computeCrestFactor(data):
    # Calculate the peak amplitude
    peak_amplitude = np.max(np.abs(data))
    # Calculate the RMS value
    rms = np.sqrt(np.mean(np.square(data)))
    # Calculate the crest factor
    crest_factor = peak_amplitude / rms
    return crest_factor


def computeShapeFactor(data):
    # Calculate the RMS value
    rms = np.sqrt(np.mean(np.square(data)))
    # Calculate the absolute average value
    avg = np.mean(np.abs(data))
    # Calculate the shape factor
    shape_factor = rms / avg
    return shape_factor


def computeImpulseFactor(data):
    peak_amplitude = np.max(np.abs(data))
    avg = np.mean(np.abs(data))
    impulse_factor = peak_amplitude/avg
    return impulse_factor


def computeMarginFactor(data):
    peak_amplitude = np.max(np.abs(data))
    temp = np.square(np.mean(np.sqrt(np.abs(data))))
    return peak_amplitude/temp


def min_max_normalize(data):
    min_val = np.min(data)
    max_val = np.max(data)
    normalized_data = (data - min_val) / (max_val - min_val)
    return normalized_data


def create_columnname(num_elements):
    array = ["c{}".format(i) for i in range(1, num_elements + 1)]
    return array


def divideArray(data, number_subsamples, overlap, overlap_percentage):
    subsamples = []
    len_subsample = len(data)//number_subsamples
    rest_subsamples = len(data) % number_subsamples
    if overlap:
        # If overlap is activated then compute the number of samples with overlaping, that means, having a percentage in common between subsamples
        if rest_subsamples == 0:
            # If the division is exact then the number of samples must be all of the same size
            i = 0
            while i<number_subsamples:
                subsamples.append(data[i*len_subsample:((i+1)*len_subsample+int(len_subsample*overlap_percentage))])
                i=i+1
        else:
            # If the division is not exact the last subsample will be greater than the rest
            i = 0
            while i<number_subsamples-1:
                subsamples.append(data[i*len_subsample:((i+1)*len_subsample+int(len_subsample*overlap_percentage))])
                i=i+1
            subsamples.append(data[i*len_subsample:(i+1)*len_subsample])
    else:
        # If overlap is deactivated
        if rest_subsamples == 0:
            # If the division is exact then the number of samples must be all of the same size
            i = 0
            while i<number_subsamples:
                subsamples.append(data[i*len_subsample:(i+1)*len_subsample])
                i=i+1
        else:
            # If the division is not exact the last subsample will be greater than the rest
            i = 0
            while i<number_subsamples-1:
                subsamples.append(data[i*len_subsample:(i+1)*len_subsample])
                i=i+1
            subsamples.append(data[i*len_subsample:(i+1)*len_subsample])
    return subsamples


def filteredFFT(order, fs, low_freq, high_freq, signal):
    nyquist = 0.5 * fs
    low = low_freq / nyquist
    high = high_freq / nyquist
    b, a = butter(order, [low, high], btype='band')
    filtered_signal = filtfilt(b, a, signal)
    envelope = np.abs(filtered_signal)
    fft_env, freq = np.abs(enter_utils.get_power_spectrum(np.hanning(len(envelope))*envelope, 20000, 0))
    return fft_env, freq


def FFT(signal, fs):
    fft_env, freq = np.abs(enter_utils.get_power_spectrum(np.hanning(len(signal))*signal, fs, 0))
    return fft_env, freq


def extractFrequencies(data, fs, fundamental, bpfo, bpfi, ftf, bsf):
    fft_filt, freq = filteredFFT(4, fs, 3500, 5000, data)
    amp_fund_filt = np.max(fft_filt[fundamental-10:fundamental+10])
    amp_bpfo_filt = np.max(fft_filt[bpfo-10:bpfo+10])
    amp_bpfi_filt = np.max(fft_filt[bpfi-10:bpfi+10])
    amp_ftf_filt = np.max(fft_filt[ftf-10:ftf+10])
    amp_bsf_filt = np.max(fft_filt[bsf-10:bsf+10])
    fft, freq = FFT(data, fs)
    amp_fund = np.max(fft[fundamental-10:fundamental+10])
    amp_bpfo = np.max(fft[bpfo-10:bpfo+10])
    amp_bpfi = np.max(fft[bpfi-10:bpfi+10])
    amp_ftf = np.max(fft[ftf-10:ftf+10])
    amp_bsf = np.max(fft[bsf-10:bsf+10])
    return amp_fund_filt, amp_bpfo_filt, amp_bpfi_filt, amp_ftf_filt, amp_bsf_filt, amp_fund, amp_bpfo, amp_bpfi, amp_bsf, amp_ftf


def getCorrelationTimeDomain(data, hi_curve):
    RMS_tmp = []
    Skewness_tmp = []
    Kurtosis_tmp = []
    CF_tmp = []
    SF_tmp = []
    IF_tmp = []
    MF_tmp = []
    for elem in data:
        RMS_tmp.append(computeRMS(elem))
        Skewness_tmp.append(computeSkewness(elem))
        Kurtosis_tmp.append(computeKurtosis(elem))
        CF_tmp.append(computeCrestFactor(elem))
        SF_tmp.append(computeShapeFactor(elem))
        IF_tmp.append(computeImpulseFactor(elem))
        MF_tmp.append(computeMarginFactor(elem))
    res = np.column_stack((hi_curve, RMS_tmp, Skewness_tmp, Kurtosis_tmp, CF_tmp, SF_tmp, IF_tmp, MF_tmp))
    df = pd.DataFrame(res)
    correlation_matrix = df.corr()
    return correlation_matrix


def getTimeCorrelationTimeDomain(data, hi_curve, num_subsamples, overlap, percentage):
    subsamples = divideArray(data, num_subsamples, overlap, percentage)
    subhicurve = divideArray(hi_curve, num_subsamples, overlap, percentage)
    res = []
    for index, subs in enumerate(subsamples):
        HI_tmp = subhicurve[index]
        RMS_tmp = []
        Skewness_tmp = []
        Kurtosis_tmp = []
        CF_tmp = []
        SF_tmp = []
        IF_tmp = []
        MF_tmp = []
        for elem in subs:
            RMS_tmp.append(computeRMS(elem))
            Skewness_tmp.append(computeSkewness(elem))
            Kurtosis_tmp.append(computeKurtosis(elem))
            CF_tmp.append(computeCrestFactor(elem))
            SF_tmp.append(computeShapeFactor(elem))
            IF_tmp.append(computeImpulseFactor(elem))
            MF_tmp.append(computeMarginFactor(elem))
        data_tmp = np.column_stack((HI_tmp, RMS_tmp, Skewness_tmp, Kurtosis_tmp, CF_tmp, SF_tmp, IF_tmp, MF_tmp))
        df_tmp = pd.DataFrame(data_tmp)
        correlation_tmp = df_tmp.corr()
        res.append(correlation_tmp[0])
    res = np.transpose(np.stack(res, axis=0))
    return res


def getCorrelationFreqDomain(data, hi_curve):
    Fundamental_Filt_tmp = []
    BPFO_Filt_tmp = []
    BPFI_Filt_tmp = []
    FTF_Filt_tmp = []
    BSF_Filt_tmp = []
    Fundamental_tmp = []
    BPFO_tmp = []
    BPFI_tmp = []
    FTF_tmp = []
    BSF_tmp = []
    for elem in data:
        f_filt, bpfo_filt, bpfi_filt, ftf_filt, bsf_filt, f, bpfo, bpfi, ftf, bsf = extractFrequencies(elem, 20000, 33, 236, 297, 15, 278)
        Fundamental_Filt_tmp.append(f_filt)
        BPFO_Filt_tmp.append(bpfo_filt)
        BPFI_Filt_tmp.append(bpfi_filt)
        FTF_Filt_tmp.append(ftf_filt)
        BSF_Filt_tmp.append(bsf_filt)
        Fundamental_tmp.append(f)
        BPFO_tmp.append(bpfo)
        BPFI_tmp.append(bpfi)
        FTF_tmp.append(ftf)
        BSF_tmp.append(bsf)
    res = np.column_stack((hi_curve, Fundamental_Filt_tmp, BPFO_Filt_tmp, BPFI_Filt_tmp, FTF_Filt_tmp, BSF_Filt_tmp, Fundamental_tmp, BPFO_tmp, BPFI_tmp, FTF_tmp, BSF_tmp))
    df = pd.DataFrame(res)
    correlation_matrix = df.corr()
    return correlation_matrix


def getCorrelationTime(data, hi_curve, num_subsamples, overlap, percentage):
    subsamples = divideArray(data, num_subsamples, overlap, percentage)
    subhicurve = divideArray(hi_curve, num_subsamples, overlap, percentage)
    res = []
    for index, subs in enumerate(subsamples):
        HI_tmp = subhicurve[index]
        Fundamental_Filt_tmp = []
        BPFO_Filt_tmp = []
        BPFI_Filt_tmp = []
        FTF_Filt_tmp = []
        BSF_Filt_tmp = []
        Fundamental_tmp = []
        BPFO_tmp = []
        BPFI_tmp = []
        FTF_tmp = []
        BSF_tmp = []
        for elem in subs:
            f_filt, bpfo_filt, bpfi_filt, ftf_filt, bsf_filt, f, bpfo, bpfi, ftf, bsf = extractFrequencies(elem, 20000, 33, 236, 297, 15, 278)
            Fundamental_Filt_tmp.append(f_filt)
            BPFO_Filt_tmp.append(bpfo_filt)
            BPFI_Filt_tmp.append(bpfi_filt)
            FTF_Filt_tmp.append(ftf_filt)
            BSF_Filt_tmp.append(bsf_filt)
            Fundamental_tmp.append(f)
            BPFO_tmp.append(bpfo)
            BPFI_tmp.append(bpfi)
            FTF_tmp.append(ftf)
            BSF_tmp.append(bsf)
        data_tmp = np.column_stack((HI_tmp, Fundamental_Filt_tmp, BPFI_Filt_tmp, BPFI_Filt_tmp, FTF_Filt_tmp, BSF_Filt_tmp, Fundamental_tmp, BPFO_tmp, BPFI_tmp, FTF_tmp, BSF_tmp))
        df_tmp = pd.DataFrame(data_tmp)
        correlation_tmp = df_tmp.corr()
        res.append(correlation_tmp[0])
    res = np.transpose(np.stack(res, axis=0))
    return res
