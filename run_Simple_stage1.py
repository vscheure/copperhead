import time
import argparse
import traceback

from coffea.processor import DaskExecutor, Runner
from coffea.nanoevents import NanoAODSchema

from stage1.SimpleProcessor import SimpleDimuonProcessor
from stage1.preprocessor import load_samples
from python.io import (
    mkdir,
    save_stage1_output_to_csv,
    delete_existing_stage1_output,
)


import dask
from dask.distributed import Client
from config.variables import variables
from functools import partial


__all__ = ["dask"]

parser = argparse.ArgumentParser()
# Slurm cluster IP to use. If not specified, will create a local cluster
parser.add_argument(
    "-sl",
    "--slurm",
    dest="slurm_port",
    default=None,
    action="store",
    help="Slurm cluster port (if not specified, " "will create a local cluster)",
)
parser.add_argument(
    "-y",
    "--year",
    dest="year",
    default="2018",
    action="store",
    help="Year to process (2016preVFP, 2016postVFP, 2017 or 2018)",
)
parser.add_argument(
    "-l",
    "--label",
    dest="label",
    default="test",
    action="store",
    help="Unique run label (to create output path)",
)
parser.add_argument(
    "-d",
    "--datasets",
    dest="datasets",
    default="UL",
    action="store",
    help="Wich datasets file to use (either UL or purdue)",
)
parser.add_argument(
    "-ch",
    "--chunksize",
    dest="chunksize",
    default=100000,
    action="store",
    help="Approximate chunk size",
)
parser.add_argument(
    "-mch",
    "--maxchunks",
    dest="maxchunks",
    default=-1,
    action="store",
    help="Max. number of chunks",
)

args = parser.parse_args()

node_ip = "128.211.149.133"  # hammer-c000
# node_ip = '128.211.149.140' # hammer-c007
dash_local = f"{node_ip}:34875"


if args.slurm_port is None:
    local_cluster = True
    slurm_cluster_ip = ""
else:
    local_cluster = False
    slurm_cluster_ip = f"{node_ip}:{args.slurm_port}"

# max number of data chunks (per dataset) to process.
# by default processing all chunks
mch = None if int(args.maxchunks) < 0 else int(args.maxchunks)



parameters = {
    # < general settings >
    "year": args.year,
    "label": args.label,
    "local_cluster": local_cluster,
    "slurm_cluster_ip": slurm_cluster_ip,
    "global_path": "/depot/cms/hmm/vscheure/",
    #
    # < input data settings >
    # 'xrootd': True,
    #'server': 'root://xrootd.rcac.purdue.edu/', # Purdue xrootd
    #'server': 'root://cmsxrootd.fnal.gov/', # FNAL xrootd
    'server': 'root://cms-xrd-global.cern.ch/',
    "xrootd": True,
    #"server": "root://eos.cms.rcac.purdue.edu/",
    "datasets_from": args.datasets,
    "chunksize": int(args.chunksize),
    "maxchunks": mch,
    #
    # < processing settings >
    "regions": ["z-peak","h-sidebands", "h-peak" ],
    "save_output": True,

}


# submit processing jobs using coffea's DaskExecutor
def submit_job(parameters):
    # mkdir(parameters["out_path"])
    out_dir = parameters["global_path"]
    mkdir(out_dir)
    out_dir += "/" + parameters["label"]
    mkdir(out_dir)
    out_dir += "/" + "stage1_output"
    mkdir(out_dir)
    out_dir += "/" + parameters["year"]
    mkdir(out_dir)

    executor_args = {"client": parameters["client"], "retries": 2}
    processor_args = {
        "samp_info": parameters["samp_infos"],
        "regions": parameters["regions"],
        "apply_to_output": partial(save_stage1_output_to_csv, out_dir=out_dir),
    }

    executor = DaskExecutor(**executor_args)
    run = Runner(
        executor=executor,
        schema=NanoAODSchema,
        chunksize=parameters["chunksize"],
        maxchunks=parameters["maxchunks"],
        xrootdtimeout=2400,
    )

    try:
        run(
            parameters["samp_infos"].fileset,
            "Events",
            processor_instance=SimpleDimuonProcessor(**processor_args),
        )

    except Exception as e:
        tb = traceback.format_exc()
        return "Failed: " + str(e) + " " + tb

    return "Success!"


if __name__ == "__main__":


    # prepare Dask client
    if parameters["local_cluster"]:
        # create local cluster
        parameters["client"] = Client(
            processes=True,
            n_workers=40,
            dashboard_address=dash_local,
            threads_per_worker=1,
            memory_limit="12GB",
        )
    else:
        # connect to existing Slurm cluster
        parameters["client"] = Client(parameters["slurm_cluster_ip"])
    print("Client created")

    # datasets to process (split into groups for convenience)
    smp = {
        # 'single_file': [
        #     'test_file',
        # ],
        "data": [
            #'test_file_data_A',
            #"data_A",
            #"data_B",
            #"data_C",
            #"data_D",
            #"data_E",
            #"data_F",
            #"data_G",
            #"data_H",
       ],
        "signal": [
            #"ggh_powheg",
            #"vbf_powheg",
           # "ggh_amcPS",
            #"vbf_powhegPS",
            #"vbf_powheg_herwig",
            #"vbf_powheg_dipole",
            #"tth",
            #"wph",
            #"wmh",
            #"zh",
        ],
        "main_mc": [
            #"dy_M-50",
            "dy_M-100To200",
            #"dy_M-50_nocut",
            #"dy_1j",
            #"dy_2j",
            #"dy_m105_160_amc",
            # "dy_m105_160_mg",
            #"dy_m105_160_vbf_amc",
            #"ewk_lljj_mll50_mjj120",
            # "ewk_lljj_mll105_160_py",
            #"ewk_lljj_mll105_160_ptj0",
            #"ewk_lljj_mll105_160_py_dipole",
            #"ttjets_dl",
            # "ewk_m50"
        ],
        "other_mc": [
            #"ttjets_dl",
            #"ttjets_sl",
            #"ttz",
            #"ttw",
            #"st_tw_top",
            #"st_tw_antitop",
            #"ww_2l2nu",
            #"wz_2l2q",
            #"wz_3lnu",
            #"wz_1l1nu2q",
            #"zz",
       ],
    }

    # select which datasets to process
    datasets_mc = []
    datasets_data = []
    for group, samples in smp.items():
        for sample in samples:
            # if sample != 'data_B':
            # if sample != 'dy_m105_160_amc':
            # if sample != "vbf_powheg_dipole":
            #    continue
            if group == "data":
                # if 'test' not in sample:
                #    continue
                # continue
                datasets_data.append(sample)
            else:
                #continue
                # if (group != "main_mc") & (group != "signal"):
                # if (group != "signal"):
                # if (group != "main_mc"):
                #    continue
                datasets_mc.append(sample)

    to_process = {"MC": datasets_mc, "DATA": datasets_data}
    for lbl, datasets in to_process.items():
        if len(datasets) == 0:
            print("No datasets!!")
            continue
        print(f"Processing {lbl}")


        # load lists of ROOT files, compute lumi weights
        parameters["samp_infos"] = load_samples(datasets, parameters)



        delete_existing_stage1_output(datasets, parameters)
        out = submit_job(parameters)

        print(out)

