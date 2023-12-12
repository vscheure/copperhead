def split_into_channels(df, v="", nochannels=False, ggHsplit = True):
    df.loc[df[f"njets_{v}"] ==-999, f"njets_{v}"] = 0.0
    df.loc[:, f"channel_{v}"] = "none"
    if nochannels == False:
        df.loc[
        (df[f"nBtagLoose_{v}"] >= 2) | (df[f"nBtagMedium_{v}"] >= 1), f"channel_{v}"
        ] = "ttHorVH"

        df.loc[
            (df[f"channel_{v}"] == "none")
            & (df[f"jj_mass_{v}"] > 400)
            & (df[f"jj_dEta_{v}"] > 2.5)
            & (df[f"jet1_pt_{v}"] > 35),
            f"channel_{v}",
        ] = "vbf"
        if ggHsplit ==True:
            df.loc[
                (df[f"channel_{v}"] == "none") & (df[f"njets_{v}"] < 1), f"channel_{v}"
            ] = "ggh_0jets"
            df.loc[
                (df[f"channel_{v}"] == "none") & (df[f"njets_{v}"] == 1.0), f"channel_{v}"
            ] = "ggh_1jet"
            df.loc[
                (df[f"channel_{v}"] == "none") & (df[f"njets_{v}"] > 1), f"channel_{v}"
            ] = "ggh_2orMoreJets"
        else:
            #print("-------------")
            #print("not splitting ggH")
            #print("-------------")
            df.loc[
                (df[f"channel_{v}"] == "none"), f"channel_{v}"
            ] = "ggh"

def categorize_by_score(df, scores, mode="uniform",year="2018", **kwargs):
    nbins = kwargs.pop("nbins", 4)
    for channel, score_names in scores.items():
        for score_name in score_names:
            score_name = f"{score_name}_{year}"
            score = df.loc[df.channel_nominal == channel, f"score_{score_name}_nominal"]
            score = df[f"score_{score_name}_nominal"]
            if mode == "uniform":
                for i in range(nbins):
                    cat_name = f"{score_name}_cat{i}"
                    cut_lo = score.quantile(i / nbins)
                    cut_hi = score.quantile((i + 1) / nbins)
                    cut = (df.channel == channel) & (score > cut_lo) & (score < cut_hi)
                    df.loc[cut, "category"] = cat_name
            if mode == "fixed_ggh":
                #df["category"] = "cat0"
                #score_ggh = df[df.loc[(df.channel_nominal == channel) & (df.dataset == "ggh_powheg"), f"score_{score_name}_nominal"]]
                signal_eff_bins = {}
                signal_eff_bins["2018"] = [0.0, 0.11045493930578232, 0.38483065366744995, 0.5410641431808472, 0.7430070638656616, 1]
                signal_eff_bins["2017"] = [0.0,  0.11117783933877945, 0.38726115226745605, 0.5426409244537354, 0.745756208896637,1]
                signal_eff_bins["2016postVFP"] = [0.0, 0.10687708854675293, 0.3635649085044861, 0.5287673473358154, 0.7236860394477844, 1]
                signal_eff_bins["2016preVFP"] = [0.0, 0.10688136518001556, 0.3617468774318695, 0.528583288192749, 0.722981870174408, 1]
                #signal_eff_bins = [0,1]
                
                #print("Score all:")
                #print(score.dropna())
                #print("Score signal")
                #print(score_ggh.dropna())
                for i in range(len(signal_eff_bins[year])-1):
                    cut_lo = signal_eff_bins[year][i]
                    cut_hi = signal_eff_bins[year][i + 1]
                    #print(f"Cut hi = {cut_hi}")
                    cat_name = f"{score_name}_cat{i}"
                    cut = (df.channel_nominal == channel) & (score > cut_lo) & (score <= cut_hi)
                    df.loc[cut, "category"] = cat_name


                
                
def categorize_dnn_output(df, score_name, channel, region, year, yearstr):
    # Run 2 (VBF yields)
    target_yields = {
        "2016": [
            0.35455259,
            0.50239086,
            0.51152889,
            0.52135985,
            0.5282209,
            0.54285134,
            0.54923751,
            0.56504687,
            0.57204477,
            0.58273066,
            0.5862248,
            0.59568793,
            0.60871905,
        ],
                "2016postVFP": [
            0.35455259,
            0.50239086,
            0.51152889,
            0.52135985,
            0.5282209,
            0.54285134,
            0.54923751,
            0.56504687,
            0.57204477,
            0.58273066,
            0.5862248,
            0.59568793,
            0.60871905,
        ],
        "2017": [
            0.44194544,
            0.55885064,
            0.57796123,
            0.58007343,
            0.58141001,
            0.58144682,
            0.57858609,
            0.59887533,
            0.59511901,
            0.59644831,
            0.59825915,
            0.59283309,
            0.57329743,
        ],
        "2018": [
            0.22036263,
            1.31808978,
            1.25396849,
            1.183724,
            1.12620194,
            1.06041376,
            0.99941623,
            0.93224412,
            0.87074753,
            0.80599462,
            0.73469265,
            0.668018,
            0.60991945,
        ],
    }

    bins = [df[score_name].max()]
    #print(bins)
    #print(channel)
    #print(region)
    #print(year)
    
    slicer = (
        (df.channel_nominal == channel) & (df.region == region) & (df.year == yearstr)
    )
    df_sorted = (
        df.loc[slicer, :]
        .sort_values(by=score_name, ascending=False)
        .reset_index(drop=True)
    )
    #print(df.loc[slicer, :][score_name])
    df_sorted["wgt_cumsum"] = df_sorted.wgt_nominal.cumsum()
    #print(df_sorted)
    tot_yield = 0
    last_yield = 0
    #print(target_yields)
    for yi in reversed(target_yields[year]):
        tot_yield += yi
        #print(yi)
        for i in range(df_sorted.shape[0] - 1):
            value = df_sorted.loc[i, "wgt_cumsum"]
            value1 = df_sorted.loc[i + 1, "wgt_cumsum"]
            #print(value)
            #print(value1)
            if (value < tot_yield) & (value1 > tot_yield):
                if abs(last_yield - tot_yield) < 1e-06:
                    continue
                if abs(tot_yield - sum(target_yields[year])) < 1e-06:
                    continue
                bins.append(df_sorted.loc[i, score_name])
                last_yield = tot_yield
    bins.append(0.0)
    bins = sorted(bins)
    #print(bins)
def categorize_dnn_output_ggh(df, score_name, channel, region, year, yearstr):
    # Run 2 (VBF yields)
    target_yields = [0,0.05,0.2,0.35,0.7,1]

    bins = [df[score_name].max()]
    #print(bins)
    #print(channel)
    #print(region)
    #print(year)
    
    slicer = (
        (df.channel_nominal == channel) & (df.region == region) & (df.year == yearstr)
    )
    df_sorted = (
        df.loc[slicer, :]
        .sort_values(by=score_name, ascending=False)
        .reset_index(drop=True)
    )
    #print(df.loc[slicer, :][score_name])
    df_sorted["wgt_cumsum_normed"] = df_sorted.wgt_nominal.cumsum()/df_sorted.wgt_nominal.sum()
    print(df_sorted)
    tot_yield = 0
    last_yield = 0
    #print(target_yields)
    for yi in (target_yields):
        for i in range(df_sorted.shape[0] - 1):
            value = df_sorted.loc[i, "wgt_cumsum_normed"]
            value1 = df_sorted.loc[i + 1, "wgt_cumsum_normed"]
            #print(value)
            #print(value1)
            if (value < yi) & (value1 > yi):
                #if abs(last_yield - tot_yield) < 1e-06:
                    #continue
                #if abs(tot_yield - sum(target_yields) < 1e-06:
                    #continue
                bins.append(df_sorted.loc[i, score_name])
                #last_yield = tot_yield
    bins.append(0.0)
    bins = sorted(bins)
    print(bins)