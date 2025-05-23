from dash import Dash, html, dash_table, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
from threading import Timer
import webbrowser
import pymupdf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import os

#----------------------------------------------------

# Initializing the app
app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

def open_browser():
    webbrowser.open_new("http://127.0.0.1:8050/")

#----------------------------------------------------

def import_excel():

    try :
        data_excel = pd.read_excel('decay.xlsx')
        time_raw     = data_excel["time [min]"].to_numpy()
        activity_raw = data_excel["Activity [mCi]"].to_numpy()
        
        selected_raw  = data_excel["Enabled"].to_numpy()
        isotopes_raw  = data_excel["Isotope"].to_numpy()
        halflives_raw = data_excel["t_1/2 [min]"].to_numpy()

        time_measured_list     = np.empty([0])
        activity_measured_list = np.empty([0])
        isotopes_list          = np.empty([0])
        halflives_list         = np.empty([0])
        
        for i in range(len(activity_raw)):
            if not np.isnan(activity_raw[i]):
                time_measured_list = np.append(time_measured_list, [time_raw[i]])
                activity_measured_list = np.append(activity_measured_list, [activity_raw[i]])
        
        for i, selected in enumerate(selected_raw):
            if selected == 1:
                isotopes_list = np.append(isotopes_list, isotopes_raw[i])
                halflives_list = np.append(halflives_list, halflives_raw[i])
        lambda_list    = np.log(2) / halflives_list
        
    except:
        print("No decay Excel file found.")
        return 0

    return time_measured_list, activity_measured_list, isotopes_list, halflives_list, lambda_list

#----------------------------------------------------

def compute_matrices(isotopes, lambda_, time_measured_list, activity_measured_list):

    num_eq = np.size(isotopes)
    time_start = 0
    time_end   = time_measured_list[-1]
    time_close = np.linspace(time_start, time_end, num_eq)

    idx = np.empty(num_eq, dtype=int)
    for i in range(num_eq):
        idx[i] = (np.abs(time_measured_list - time_close[i])).argmin()

    time     = time_measured_list[idx]
    activity = activity_measured_list[idx]

    #--------------------

    a = np.empty([num_eq, num_eq])
    b = np.empty(num_eq)

    for i in range(num_eq):
        for j in range(num_eq):
            a[i][j] = lambda_[j]*np.exp(-lambda_[j]*time[i])
        b[i] = activity[i]
    
    N_0 = np.linalg.solve(a, b)
    A_0 = N_0 * lambda_
    
    #--------------------
    
    debug = False
    if debug == True:
        print("Time list [min] : " + str(time_measured_list))
        print("Activity list [mCi] : " + str(activity_measured_list))
        print()

        print("Selected time [min] : " + str(time))
        print("Selected activity [mCi] : " + str(activity))
        print()

    #--------------------    

    return N_0, A_0

def main():

    time_measured_list, activity_measured_list, isotopes_list, halflives_list, lambda_list = import_excel()
    file_result = open("result.txt", "w")
    log_length = 30 # Max expected number of iterations
    log_A0 = np.zeros((np.size(isotopes_list), log_length), dtype=float)

    #--------------------

    selected_isotopes_bool = np.full(np.size(isotopes_list), True) # Create bool array of True values
    result_ok = 0
    iteration = 0

    while result_ok == 0:
    
        isotopes  = isotopes_list[selected_isotopes_bool]
        lambda_   = lambda_list[selected_isotopes_bool]
        num_eq = np.size(isotopes)

        #--------------------  
        # Matrices resolution

        N_0, A_0 = compute_matrices(isotopes, lambda_, time_measured_list, activity_measured_list)
        iteration += 1

        index_activity_min = np.argmin(A_0)
        true_array_index = 0
        for i, bool in enumerate(selected_isotopes_bool):
            if bool == True:
                if true_array_index == index_activity_min:
                    selected_isotopes_bool[i] = False
                true_array_index += 1

        if A_0[index_activity_min] >= 0:
            result_ok = 1
        
        #--------------------
        # Interpolation

        t = np.arange(int(time_measured_list[-1] * 1.1))
        N_extrapolate = np.empty([num_eq, np.size(t)])
        A_extrapolate = np.empty([num_eq, np.size(t)])
        A_extrapolate_tot = np.empty(np.size(t))
        for i in range(num_eq):
            N_extrapolate[i] = N_0[i] * np.exp(-lambda_[i]*t)
            A_extrapolate[i] = N_extrapolate[i] * lambda_[i]
        A_extrapolate_tot = np.sum(A_extrapolate, axis=0)

        #--------------------
        # Error computation with measured value
        e_array = 100 * np.abs(A_extrapolate_tot[time_measured_list.astype(int)] - activity_measured_list) / activity_measured_list
        e_mean = np.mean(e_array)

        #--------------------
        # Result log

        # If I want to add a graph for the iterations
        for i in range(np.size(A_0)):
            log_A0[np.where(isotopes_list == isotopes[i]), iteration-1] = A_0[i]

        str_intro = str("---- Iteration " + str(iteration) + " : Activity EOB ---- \n" + 
                        "Mean error : " + "{:.2f}".format(e_mean) + "% \n" + 
                        "Worse error : " + "{:.2f}".format(np.max(e_array)) + "% \n\n")
        str_result = []
        for i in range(np.size(A_0)):
            str_result.append(str(isotopes[i]) + " : " + "{:.2f}".format(A_0[i]) + " [mCi] \n")
        str_result.append(str("\n\n"))

        print(str_intro, end="")
        for i in str_result:
            print(i, end="")

        file_result.write(str_intro)
        file_result.writelines(str_result)
    
    #--------------------

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=time_measured_list, y=activity_measured_list, name="Measures", mode ="markers"))
    fig.add_trace(go.Scatter(x=t, y=A_extrapolate_tot, name="Total", mode ="lines"))
    for i in range(num_eq):
        fig.add_trace(go.Scatter(x=t, y=A_extrapolate[i], name=isotopes[i], mode ="lines"))

    fig.update_layout(
            xaxis = dict(title=dict(text="Time [min]")),
            yaxis = dict(title=dict(text="Activity [mCi]")),
            legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
            title="Decay over time")

    file_result.close()
    fig.show()

#----------------------------------------------------

if __name__ == "__main__":
    main()

#----------------------------------------------------