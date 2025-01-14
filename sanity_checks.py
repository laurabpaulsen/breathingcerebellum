import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd


def plot_intensity(df):
    fig, ax = plt.subplots(1, 1, figsize = (10, 6), dpi = 300)


    # correct
    correct= df[df["correct"] == 1]
    ax.scatter(correct["time"], correct["intensity"], c = "green", label = "correct response", s = 7)

    #incorrect 
    incorrect = df[df["correct"] == 0]
    ax.scatter(incorrect["time"], incorrect["intensity"], c = "red", label = "incorrect incorrect", s = 7)

    df_weak = df[df["event_type"]== "target/weak"]
    ax.plot(df_weak["time"], df_weak["intensity"], c = "k", alpha = 0.7, linewidth = 1)

    

    ax.set_ylabel("Stimuli intensity")
    ax.set_xlabel("Time (s)")

    ax.legend()

    plt.savefig("fig/QUEST.png")


def check_timing(df):
    fig, ax = plt.subplots(1, 1, figsize = (10, 6), dpi = 300)

    df= df[df["event_type"].isin([ "stim/salient", "target/weak", "target/omis"])]
    df["time_diff"]=  df["time"].diff()

    # get the different in time between all events and plot it 
    time_diff = df["time"].diff()
    for diff in time_diff:
        ax.axvline(diff, alpha = 0.1, linewidth = 0.2)

    ax.set_xlim((0, 1.1))
    



    plt.savefig("fig/timing.png")




if __name__ in "__main__":
    filename = Path("output/test.csv")

    df = pd.read_csv(filename)
    print(df.columns)
    print(df.head())

    plot_intensity(df)
    check_timing(df)