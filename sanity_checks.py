import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd


def plot_intensity(df):
    fig, ax1 = plt.subplots(1, 1, figsize=(10, 6), dpi=300)

    # primary y-axis: Stimuli intensity
    # correct responses (of weak)
    correct = df[(df["correct"] == 1) & (df["intensity"] > 0)] 
    ax1.scatter(correct["time"], correct["intensity"], c="green", label="Correct response", s=7)

    # incorrect responses of weak
    incorrect = df[(df["correct"] == 0) & (df["intensity"] > 0)]
    ax1.scatter(incorrect["time"], incorrect["intensity"], c="red", label="Incorrect response", s=7)

    # target/weak events
    df_weak = df[(df["event_type"] == "target/left") | (df["event_type"] == "target/right")]
    ax1.plot(df_weak["time"], df_weak["intensity"], c="k", alpha=0.7, linewidth=1)

    ax1.set_ylabel("Stimuli intensity")
    ax1.set_xlabel("Time (S)")
    ax1.legend(loc="upper left")

    # secondary y-axis: ISI
    ax2 = ax1.twinx()
    ax2.plot(df_weak["time"], df_weak["ISI"], c="gray", alpha=0.7, linewidth=1, linestyle="--")
    ax2.set_ylabel("Inter-Stimulus Interval (ISI)", color="gray")
    ax2.tick_params(axis='y', labelcolor="gray")

    # Save the figure
    plt.savefig("fig/QUEST.png")

def check_timing(df):
    fig, ax = plt.subplots(1, 1, figsize = (10, 6), dpi = 300)

    for diff in df["time_diff"]:
        ax.axvline(diff, alpha = 0.1, linewidth = 0.2)

    ax.set_xlim((0, 1.5))

    plt.savefig("fig/timing.png")


if __name__ == "__main__":
    filename = Path("output_b/test_SGC.csv")
    df = pd.read_csv(filename)

    plot_intensity(df)

    # Filter relevant event types and make a copy to avoid SettingWithCopyWarning
    df_check_timing = df[df["event_type"].isin(["stim/salient", "target/left", "target/right"])].copy()

    # Loop over blocks and compute time differences
    for block in df_check_timing["block"].unique():
        df_tmp = df_check_timing[df_check_timing["block"] == block].copy()

        df_tmp["time_diff"] = df_tmp["time"].diff()

        max_diff = df_tmp['time_diff'].max()
        min_diff = df_tmp['time_diff'].min()
        diff_range = max_diff - min_diff

        print(
            f"Block {block} — Max: {round(max_diff, 4)}, Min: {round(min_diff, 4)}, Diff: {round(diff_range, 4)}"
        )
    
    # Compute time_diff across the entire filtered DataFrame
    df_check_timing["time_diff"] = df_check_timing["time"].diff()

    check_timing(df_check_timing)