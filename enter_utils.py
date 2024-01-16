import os
import numpy as np
from matplotlib import pyplot as plt
from scipy import fft
import keras
from keras.layers import Input, Dense
import tensorflow as tf
from keras import layers
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean
import matlab.engine
from scipy.signal import butter, filtfilt, argrelextrema
import pandas as pd
from keras.models import Model


def getDataset(name, samples, first_sample):
    data = np.array(pd.read_csv('prog_analizador/data/'+str(name)+'.csv', header=None, index_col=None))
    denoised_data = np.array(pd.read_csv('prog_analizador/data/healthy'+str(name)+'.csv', header=None, index_col=None))
    return data[int(first_sample):int(first_sample)+int(samples)], denoised_data


def getDatasetNew(name, samples, first_sample, user):
    data = np.array(pd.read_csv('prog_analizador/saved_data/' + user + '/' +str(name)+'.csv', header=None, index_col=None))
    denoised_data = np.array(pd.read_csv('prog_analizador/saved_data/' + user + '/healthy' +str(name)+'.csv', header=None, index_col=None))
    return data[int(first_sample):int(first_sample)+int(samples)], denoised_data


def getNMax(name, user):
    data = np.array(pd.read_csv('prog_analizador/saved_data/' + user + '/' +str(name), header=None, index_col=None))
    return data.shape[0]


def createModel(name, input_data):
    input_layer = Input(shape=(input_data.shape[0],))
    encoder = MonotonicityLayer(units=3500)(input_layer)
    encoder = Dense(700, activation='sigmoid')(encoder)
    encoder = SmoothingLayer(200)(encoder)
    encoder = Dense(1, activation='sigmoid')(encoder)
    encoder = Model(input_layer, encoder)
    encoder.compile(optimizer='adam', loss='mse')
    tf.keras.models.save_model(encoder, str(name))
    return encoder


def get_power_spectrum(data, fs, padding=0):
    xdft, freqs = _get_two_sided_amplitude_spectrum(data, fs, padding)

    xdft = xdft * xdft
    return xdft, freqs


def _get_two_sided_amplitude_spectrum(data, fs, n_padding):
    N = len(data) + n_padding
    xdft = fft.rfft(data, n=N, norm="forward")
    freqs = fft.rfftfreq(N, d=1./fs)
    return xdft, freqs


class MonotonicityLayer2(layers.Layer):
    def __init__(self, units, **kwargs):
        super(MonotonicityLayer2, self).__init__(**kwargs)
        self.units = units

    def build(self, input_shape):
        self.mask = self.add_weight(name="adfsadfa", shape=input_shape[1:], initializer=tf.keras.initializers.Ones(), trainable=True)
        super(MonotonicityLayer2, self).build(input_shape)

    def call(self, inputs):
        masked_inputs = tf.multiply(inputs, self.mask)
        return masked_inputs

    def compute_output_shape(self, input_shape):
        return input_shape


def from_config(config):
    return MonotonicityLayer2(**config)


class SmoothingLayer(keras.layers.Layer):
    def __init__(self, window_size):
        super(SmoothingLayer, self).__init__()
        self.window_size = window_size

    def call(self, inputs):
        inputs = inputs
        smoothed_output = tf.nn.moments(inputs, axes=[1], keepdims=True)[1]
        return smoothed_output


def differenceSignals(signal1, signal2):
    euc = euclidean(signal1, signal2)
    distance, path = fastdtw(signal1, signal2, dist=euc)
    new_signal = np.zeros(len(signal1))
    for point in path:
        x, y = point
        new_signal[y] = signal2[y]-signal1[x]
    return new_signal


def compute_pdf(time_series):
    hist, bin_edges = np.histogram(time_series, bins='auto', density=True)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    return bin_centers, hist


def find_threshold_using_percentile(pdf_values, percentile):
    threshold = np.percentile(pdf_values, percentile)
    return threshold


def getThreshold(data):
    pdf_x, pdf_y = compute_pdf(data)
    threshold = find_threshold_using_percentile(pdf_x, 95)
    return threshold


def checkStage(HI_analyzed_samples, threshold):
    counter = 0
    faulty = False
    bk = None
    for index, elem in enumerate(HI_analyzed_samples):
        if elem >= threshold:
            counter = counter + 1
            if counter >= 5:
                bk = index
                faulty = True
                break
        else:
            counter = 0
    return faulty, bk


def computeKurtogram(data, fs, level):
    eng = matlab.engine.start_matlab()
    kurtogram_values = eng.kurtogram(data, fs, level)
    return kurtogram_values


def filteredFFT(order, fs, low_freq, high_freq, signal):
    nyquist = 0.5 * fs
    low = low_freq / nyquist
    high = high_freq / nyquist
    b, a = butter(order, [low, high], btype='band')
    filtered_signal = filtfilt(b, a, signal)
    envelope = np.abs(filtered_signal)
    fft_env, freq = np.abs(get_power_spectrum(np.hanning(len(envelope))*envelope, fs, 0))
    fft_env[0:5] = 0
    return fft_env, freq


def getFilterBands(vals, fs, init_level):
    vals2 = [np.array(d) for d in vals]
    vals2 = np.stack(vals2, axis=1)[0]
    for elem in vals2:
        first = elem[0]
        last = elem[len(elem)-1]
        vals2[vals2 == first] = 0
        vals2[vals2 == last] = 0
    indices = np.where(vals2[init_level:] == vals2[init_level:].max())
    first_position = indices[1][0] % len(vals2[0])
    last_position = indices[1][len(indices[1])-1] % len(vals2[0])
    first_frequency = fs/2/len(vals2[0])*first_position
    last_frequency = fs/2/len(vals2[0])*(last_position+1)
    return first_frequency, last_frequency


def common_member(a, b):
    result = [i for i in a if i in b]
    return result


def determineFailure(ruta_carpeta, data, healthydata, hi_value, fs, fstart, fend, freq_interests, interval):
    bpfo_freq = [freq_interests[0], freq_interests[0]*2, freq_interests[0]*3, freq_interests[0]*4, freq_interests[0]*5, freq_interests[0]*6]
    bpfi_freq = [freq_interests[1], freq_interests[1]*2, freq_interests[1]*3, freq_interests[1]*4, freq_interests[1]*5, freq_interests[1]*6]
    bsf_freq = [freq_interests[2], freq_interests[2]*2, freq_interests[2]*3, freq_interests[2]*4, freq_interests[2]*5, freq_interests[2]*6]
    ftf_freq = [freq_interests[3], freq_interests[3]*2, freq_interests[3]*3, freq_interests[3]*4, freq_interests[3]*5, freq_interests[3]*6]
    freq_total = np.concatenate([bpfo_freq, bpfi_freq, bsf_freq, ftf_freq])

    fft_f, freqs = filteredFFT(4, fs, fstart, fend, data)
    indices = argrelextrema(fft_f, np.greater)
    amplitudes = []
    for elem in indices[0]:
        amplitudes.append(fft_f[elem])
    ind = np.argsort(amplitudes)[::-1][:10]
    top10 = indices[0][ind]
    important_f_real_peaks = []
    important_f_expected_peaks = []
    for freq in freq_total:
        for elem in top10:
            elem = int(elem*(freqs[1]-freqs[0]))
            if elem >= freq-interval and elem <= freq+interval:
                important_f_real_peaks.append(elem)
                important_f_expected_peaks.append(freq)

    fft_nf, freqs = get_power_spectrum(data, fs)
    indices = argrelextrema(fft_nf, np.greater)
    amplitudes = []
    for elem in indices[0]:
        amplitudes.append(fft_nf[elem])
    ind = np.argsort(amplitudes)[::-1][:10]
    top10 = indices[0][ind]
    important_nf_real_peaks = []
    important_nf_expected_peaks = []
    for freq in freq_total:
        for elem in top10:
            elem = int(elem*(freqs[1]-freqs[0]))
            if elem >= freq-interval and elem <= freq+interval:
                important_nf_real_peaks.append(elem)
                important_nf_expected_peaks.append(freq)

    bpfo_status = 0
    bpfi_status = 0
    bsf_status = 0
    ftf_status = 0
    if (len(important_f_expected_peaks) > 0):
        if (len(common_member(important_f_expected_peaks, bpfo_freq)) > 0):
            bpfo_status = bpfo_status+1
        if (len(common_member(important_f_expected_peaks, bpfi_freq)) > 0):
            bpfi_status = bpfi_status+1
        if (len(common_member(important_f_expected_peaks, bsf_freq)) > 0):
            bsf_status = bsf_status+1
        if (len(common_member(important_f_expected_peaks, ftf_freq)) > 0):
            ftf_status = ftf_status+1
    if (len(important_nf_expected_peaks) > 0):
        if (len(common_member(important_nf_expected_peaks, bpfo_freq)) > 0):
            bpfo_status = bpfo_status+2
        if (len(common_member(important_nf_expected_peaks, bpfi_freq)) > 0):
            bpfi_status = bpfi_status+2
        if (len(common_member(important_nf_expected_peaks, bsf_freq)) > 0):
            bsf_status = bsf_status+2
        if (len(common_member(important_nf_expected_peaks, ftf_freq)) > 0):
            ftf_status = ftf_status+2

    pdf_x, pdf_y = compute_pdf(healthydata)
    early_threshold = find_threshold_using_percentile(pdf_x, 95)
    mid_threshold = np.max(healthydata)+(np.max(healthydata)-early_threshold)*50
    last_threshold = np.max(healthydata)+(np.max(healthydata)-early_threshold)*100
    stop = False

    result = {
        'fault_detected': False,
        'fault_info': None,
        'fault_type': [],
        'fault_details': [],
        'analysis_result': None
    }

    if (hi_value < early_threshold):
        result['analysis_result'] = "No fault detected"
        stop = True
    elif (hi_value < mid_threshold):
        result['fault_info'] = "A fault has been detected in an early stage"
    elif (hi_value < last_threshold):
        result['fault_info'] = "A fault has been detected in a medium stage"
    else:
        result['fault_info'] = "A fault has been detetcetd in a last degradation stage"

    if not stop:
        if (bpfo_status+bpfi_status+ftf_status+bsf_status == 0):
            result['analysis_result'] = "There is no failure detected, and the motor is completely healthy"
        else:
            result['fault_detected'] = True
            result['analysis_result'] = "A fault has been detected"

            if (bpfo_status > 0):
                result['fault_type'].append("Outer_race")
                if (len(common_member(important_f_expected_peaks, bpfo_freq))>0):
                    result['fault_details'].append(common_member(important_f_expected_peaks, bpfo_freq))
                    generateImg(common_member(important_f_expected_peaks, bpfo_freq), fft_f, freqs, ruta_carpeta, 1, "Outer-race")
                elif (len(common_member(important_nf_expected_peaks, bpfo_freq))>0):
                    result['fault_details'].append(common_member(important_nf_expected_peaks, bpfo_freq))
                    generateImg(common_member(important_nf_expected_peaks, bpfo_freq), fft_f, freqs, ruta_carpeta, 1, "Outer-race")
            if (bpfi_status > 0):
                result['fault_type'].append("Inner_race")
                if (len(common_member(important_f_expected_peaks, bpfi_freq))>0):
                    result['fault_details'].append(common_member(important_f_expected_peaks, bpfi_freq))
                    generateImg(common_member(important_f_expected_peaks, bpfi_freq), fft_f, freqs, ruta_carpeta, 2, "Inner-race")
                elif (len(common_member(important_nf_expected_peaks, bpfi_freq))>0):
                    result['fault_details'].append(common_member(important_nf_expected_peaks, bpfi_freq))
                    generateImg(common_member(important_nf_expected_peaks, bpfi_freq), fft_f, freqs, ruta_carpeta, 2, "Inner-race")
            if (bsf_status > 0):
                result['fault_type'].append("Bearing_Balls")
                if (len(common_member(important_f_expected_peaks, bsf_freq))>0):
                    result['fault_details'].append(common_member(important_f_expected_peaks, bsf_freq))
                    generateImg(common_member(important_f_expected_peaks, bsf_freq), fft_f, freqs, ruta_carpeta, 3, "Bearing Balls")
                elif (len(common_member(important_nf_expected_peaks, bsf_freq))>0):
                    result['fault_details'].append(common_member(important_nf_expected_peaks, bsf_freq))
                    generateImg(common_member(important_nf_expected_peaks, bsf_freq), fft_f, freqs, ruta_carpeta, 3, "Bearing Balls")
            if (ftf_status > 0):
                result['fault_type'].append("Cage")
                if (len(common_member(important_f_expected_peaks, ftf_freq))>0):
                    result['fault_details'].append(common_member(important_f_expected_peaks, ftf_freq))
                    generateImg(common_member(important_f_expected_peaks, ftf_freq), fft_f, freqs, ruta_carpeta, 4, "Cage")
                elif (len(common_member(important_nf_expected_peaks, ftf_freq))>0):
                    result['fault_details'].append(common_member(important_nf_expected_peaks, ftf_freq))
                    generateImg(common_member(important_nf_expected_peaks, ftf_freq), fft_f, freqs, ruta_carpeta, 4, "Cage")

    return result


def generateImg(members, fft_env, freq, carpeta, flag, name):
    plt.figure()

    for member in members:
        plt.axvline(member, color="red")

    last_member = int(members[-1])

    if (last_member*5 > 5000):
        plt.plot(freq[0:5000], fft_env[0:5000], color="blue")
    else:
        plt.plot(freq[0:last_member*5], fft_env[0:last_member*5], color="blue")

    plt.title(name)
    plt.savefig(os.path.join(carpeta, f'plot{flag}.png'))
