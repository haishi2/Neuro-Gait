import pandas as pd
import numpy as np
from scipy.signal import butter, filtfilt
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

import os
import glob
import re
from datetime import datetime
import time 

from t import *



def extract_timestamp(filename):
    match = re.search(r'(\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})', filename)
    if match:
        return datetime.strptime(match.group(1), "%Y-%m-%d-%H-%M-%S")
    return None  


def getLatestCsvs(directory):

    r_files = glob.glob(os.path.join(directory, 'R*.csv'))
    l_files = glob.glob(os.path.join(directory, 'L*.csv'))
    
    latest_r_csv = max(r_files, key=os.path.getmtime) if r_files else None
    latest_l_csv = max(l_files, key=os.path.getmtime) if l_files else None
    
    return latest_r_csv, latest_l_csv
    
def getAllCsvsPairs(directory):
    
    r_files = glob.glob(os.path.join(directory, 'R*.csv'))
    l_files = glob.glob(os.path.join(directory, 'L*.csv'))
    
    r_files.sort(key=lambda f: extract_timestamp(f))
    l_files.sort(key=lambda f: extract_timestamp(f))
    
    paired_csvs = list(zip(r_files, l_files))
    
    return paired_csvs
    
def getData(r, l):
    column_names = ['ax', 'ay', 'az', 'gx', 'gy', 'gz','t']
    fs=10
    dfL = pd.read_csv(l, names=column_names, header=None) # change filename to pull datetime
    dfR = pd.read_csv(r, names=column_names, header=None) # change filename to pull datetime

    num_rowsL = dfL.shape[0]
    num_rowsR = dfR.shape[0]

    min_rows = min(num_rowsL, num_rowsR)

    if num_rowsL > min_rows:
        dfL = dfL.iloc[-min_rows:]

    if num_rowsR > min_rows:
        dfR = dfR.iloc[-min_rows:]

    print(dfL.head())
    print(dfR.head())

    gyL_v = np.array(dfL[['gy']]).flatten()
    tL_v = np.array(dfL[['t']]).flatten()

    gyR_v = np.array(dfR[['gy']]).flatten()
    tR_v = np.array(dfR[['t']]).flatten()
    
    # CLEANING DATA

    def butter_lowpass_filter(data, cutoff=5, fs=100, order=4):
        nyquist = 0.5 * fs  # Nyquist Frequency
        normal_cutoff = cutoff / nyquist
        b, a = butter(order, normal_cutoff, btype='low', analog=False)
        return filtfilt(b, a, data)

    gyL_v_f = butter_lowpass_filter(gyL_v, cutoff = 1, fs = fs, order=3)
    gyR_v_f = butter_lowpass_filter(gyR_v, cutoff = 1, fs = fs, order=3)
    
    # DETECTING HS AND TO POINTS

    HS_IndicesL, _ = find_peaks(-gyL_v_f, prominence=0.5)
    TO_IndicesL, _ = find_peaks(gyL_v_f, prominence=0.5)

    minDataL = min(len(HS_IndicesL), len(TO_IndicesL))
    HS_IndicesL = HS_IndicesL[:minDataL]
    TO_IndicesL = TO_IndicesL[:minDataL]

    HS_TimesL = tL_v[HS_IndicesL]
    TO_TimesL = tL_v[TO_IndicesL]

    HS_IndicesR, _ = find_peaks(-gyR_v_f, prominence=0.5)
    TO_IndicesR, _ = find_peaks(gyR_v_f, prominence=0.5)

    minDataR = min(len(HS_IndicesR), len(TO_IndicesR))
    HS_IndicesR = HS_IndicesR[:minDataR]
    TO_IndicesR = TO_IndicesR[:minDataR]

    HS_TimesR = tR_v[HS_IndicesR]
    TO_TimesR = tR_v[TO_IndicesR]
    
    # CALCULATING BASIC GAIT PARAMETERS

    strideTimesL = np.diff(HS_TimesL)
    avgStrideDurationL = np.mean(strideTimesL)

    strideTimesR = np.diff(HS_TimesR)
    avgStrideDurationR = np.mean(strideTimesR)

    avgStrideDuration = (avgStrideDurationL + avgStrideDurationR) / 2

    stanceTimesL = np.abs(TO_TimesL - HS_TimesL) + (1 / fs)
    avgStanceDurationL = np.mean(stanceTimesL)

    stanceTimesR = np.abs(TO_TimesR - HS_TimesR) + (1 / fs)
    avgStanceDurationR = np.mean(stanceTimesR)

    avgStanceDuration = (avgStanceDurationL + avgStanceDurationR) / 2

    minDataL = min(len(strideTimesL), len(stanceTimesL))
    swingTimesL = strideTimesL[:minDataL] - stanceTimesL[:minDataL]
    avgSwingDurationL = np.mean(swingTimesL)

    minDataR = min(len(strideTimesR), len(stanceTimesR))
    swingTimesR = strideTimesR[:minDataR] - stanceTimesR[:minDataR]
    avgSwingDurationR = np.mean(swingTimesR)

    avgSwingDuration = (avgSwingDurationL + avgSwingDurationR) / 2


    NumStridesL = (tL_v[-1] - tL_v[0])/avgStrideDurationL;
    NumStridesR = (tR_v[-1] - tR_v[0])/avgStrideDurationR;

    avgNumStrides = (NumStridesR + NumStridesR) / 2;

    avgCadenceL = NumStridesL/((tL_v[-1] - tL_v[0])/60);
    avgCadenceR = NumStridesR/((tR_v[-1] - tR_v[0])/60);

    avgCadence = (avgCadenceL + avgCadenceR) / 2
    print(avgCadence)

    # CALCULATING COMPLEX GAIT VARIABLES

    SDeviationL = np.std(strideTimesL, ddof=1)
    SDeviationR = np.std(strideTimesR, ddof=1)
    SDeviation = (SDeviationL + SDeviationR) / 2

    CoeffVariationL = (SDeviationL / np.mean(strideTimesL)) * 100
    CoeffVariationR = (SDeviationR / np.mean(strideTimesR)) * 100

    gaitVariability = (CoeffVariationR + CoeffVariationL) / 2
    gaitAsymmetry = 100 * abs(np.log(avgSwingDurationR / avgSwingDurationL))
    print(gaitVariability)
    # ACTIVITY DETECTION

    walkingSpeed = 57 # change this to be avg cadence pulled from database
    walkingStrideDuration = 1 / (walkingSpeed / 60)

    fastWalkingStrideDuration = 0.75 * walkingStrideDuration
    runningStrideDuration = 0.5 * walkingStrideDuration

    stairSpeed = 0.5 * walkingSpeed
    stairStrideDuration = 1 / (stairSpeed / 60)

    min_len = min(len(tL_v), len(strideTimesL))
    tL_v = tL_v[:min_len]
    strideTimesL = strideTimesL[:min_len]

    # Initialize 2D array (object type for mixed time & string)
    activity = np.empty((min_len, 2), dtype=object)

    # Assign time values from 't' to the first column
    activity[:, 0] = tL_v

    # Assign activity labels based on stride time conditions
    for i in range(min_len):
        strideTime = strideTimesL[i]
        if 0.75 * fastWalkingStrideDuration <= strideTime <= 1.25 * fastWalkingStrideDuration:
            activity[i, 1] = "Fast Walking"
        elif 0.9 * stairStrideDuration <= strideTime <= 1.1 * stairStrideDuration:
            activity[i, 1] = "Climbing/Descending Stairs"
        elif 0.75 * walkingStrideDuration <= strideTime <= 1.25 * walkingStrideDuration:
            activity[i, 1] = "Walking"
        else:
            activity[i, 1] = "Stationary"
    np.set_printoptions(threshold=np.inf)
    print(activity)

    # ADD PART TO OUTPUT
    
    obj = {
        "time": r.split("\\")[1],
        "avgStrideDuration": avgStrideDuration,
        "avgStanceDuration": avgStanceDuration,
        "avgSwingDuration": avgSwingDuration,
        "avgCadence": avgCadence,
        "gaitVariability": gaitVariability,
        "gaitAsymmetry": gaitAsymmetry,
        "isFlagged": False,
        "activity": []
    }
    
    return obj



def withinRatio(val1, val2, thresh):
    lower = val2 * (1-thresh)
    upper = val2 * (1+thresh)
    return (val1 <= upper)
    
def flaggingSystem(name, collection):
    patient = get_patient(name, collection)
    if patient == None:
        return 0
        
    averages = patient['gait_info']
    
    thresh = 0.15
    print(averages)
    newRecs = []
    flags = 0
    count = 0
    for rec in patient['Recordings']:
        if not (withinRatio(rec['gaitVariability'], averages['gaitVariability'], 0.65) and withinRatio(rec['gaitAsymmetry'], averages['gaitAsymmetry'], 0.65)):
            rec['isFlagged'] = True
            flags += 1
            newRecs.append(rec)
        else:
            newRecs.append(rec)
        count += 1
    
    print(flags)
    finalCount = count - flags
    
    newObj = {
        'Name': patient['Name'],
        'Recordings': newRecs,
        'num_recordings_non_flag': finalCount
    }
    update_patient_info(newObj, False, collection)
        
    
    
def uploadCSV(name, directory, collection):
    patient = get_patient(name, collection)
    if patient == None:
        return 0
    entries = getAllCsvsPairs(directory)
    numEntries = len(entries)
    count = 0
    newRecs = []
    for r,l in entries:
        o = getData(r,l)
        newRecs.append(o)
        if not o["isFlagged"]:
            count += 1
            
    currentCount = patient['num_recordings_non_flag']
    currentRecs = patient['Recordings']
    
    finalCount = count + currentCount
    finalRec =  newRecs + currentRecs
    
    
    newObj = {
        'Name': patient['Name'],
        'Recordings': finalRec,
        'num_recordings_non_flag': finalCount
    }
    update_patient_info(newObj, False, collection)
    return count
    
    
def updateAverages(name, collection):
    patient = get_patient(name, collection)
    if patient == None:
        return 0
    
    count = 0
    avgCad = 0
    gaitVar = 0
    gaitAsym = 0
    
    currentRecs = patient['Recordings']
    for r in currentRecs:
        if r['isFlagged']:
            continue
        avgCad += r['avgCadence']
        gaitVar += r['gaitVariability']
        gaitAsym += r['gaitAsymmetry']
        count+= 1
    if count == 0:
        return 0;
    obj = {'avgCadence' : avgCad / count, 'gaitVariability': gaitVar / count, 'gaitAsymmetry': gaitAsym / count}
    newObj = {'Name': patient['Name'], 'gait_info': obj}
    
    update_patient_info(newObj, False, collection)

    
    
if __name__ == "__main__":
    client = pymongo.MongoClient("mongodb+srv://shihai797:d6BK2dVfUSBHCxHc@fullstackopen-pt3.vx18ygi.mongodb.net/?retryWrites=true&w=majority&appName=fullstackopen-pt3")

    db = client['Neuro-Gait']

    collection = db['Patients']
    
    names = ["Taylor Reed", "Alex Carter", "Jordan Smith"]
    
