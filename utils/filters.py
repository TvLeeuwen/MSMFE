def filter_states(df, filter_params):
    filtered = [
        col
        for col in df.columns
        if ("time" not in col.lower())
        and (
            any(f in col.lower() for f in filter_params["state_filters"])
            == filter_params["invert_filter"]
        )
    ]
    df[filtered] = 0
    return df


def filter_states_visualization(df, filter_params):
    filtered = [
        col
        for col in df.columns
        if ("time" not in col.lower())
        and (
            any(f in col.lower() for f in filter_params["state_filters"])
            != filter_params["invert_filter"]
        )
    ]
    filtered = ["time"] + filtered
    df_filtered = df[filtered]
    return df_filtered
