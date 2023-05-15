#!/usr/bin/env python

import sys
import os
import pwd
import time
from Pegasus.api import *
from datetime import datetime
from argparse import ArgumentParser

class CASAWorkflow(object):
    def __init__(self, outdir, forecast_fn):
        self.outdir = outdir
        self.forecast_fn = forecast_fn

    def generate_dax(self):
        "Generate a workflow"
        ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        # wf = Workflow(f"casa_nowcast-wf-{ts}")

        wf = Workflow(f"casa_nowcast-wf")
        wf.add_metadata(name="CASA Nowcast")

        #extract time
        string_end = self.forecast_fn[-1].find(".")
        file_time = self.forecast_fn[-1][string_end-12:string_end]
        file_time = file_time + "00"
        file_ymd = file_time[0:8]
        file_hms = file_time[8:14]


        #convert to individual minute files
        forecast_file = File(self.forecast_fn[-1])
        nowcast_split_job = Job("NowcastToWDSS2")\
                        .add_args(self.forecast_fn[-1],".",)\
                        .add_inputs(forecast_file)
        for x in range(31):
            pr_file = File("PredictedReflectivity_"+ str(x) + "min_" + file_ymd + "-" + file_hms + ".nc")
            nowcast_split_job.add_outputs(pr_file)
            # transfer=True, register=False
                    
        wf.add_jobs(nowcast_split_job)
        
        #run merged reflectivity threshold
        mrtconfigfile = File("mrtV2_config.txt")
        for x in range(31):
            pr_fn = "PredictedReflectivity_"+ str(x) + "min_" + file_ymd + "-" + file_hms + ".nc"
            pr_file = File(pr_fn)
            pr_geojson = File("mrt_STORM_CASA_" + str(x) + "_" + file_ymd + "-" + file_hms + ".geojson")
            
            mrt_job = Job("mrtV2")\
                    .add_args("-c",mrtconfigfile,pr_fn)\
                    .add_inputs(mrtconfigfile,pr_file)\
                    .add_outputs(pr_geojson)\
                    .add_profiles(Namespace.PEGASUS, key="label", value=f"label_{str(x)}")

            wf.add_jobs(mrt_job)
        
        # generate image from max reflectivity
        colorscale = File("nexrad_ref.png")
        for x in range(31):
            pr_file = File("PredictedReflectivity_"+ str(x) + "min_" + file_ymd + "-" + file_hms + ".nc")
            pr_image = File("PredictedReflectivity_"+ str(x) + "min_" + file_ymd + "-" + file_hms + ".png")
            pr_image_job = Job("merged_netcdf2png")\
                        .add_args("-c", colorscale, "-q 235 -z 0,75", "-o", pr_image, pr_file)\
                        .add_inputs(pr_file, colorscale)\
                        .add_outputs(pr_image)\
                        .add_profiles(Namespace.PEGASUS, key="label", value=f"label_{str(x)}")
            wf.add_jobs(pr_image_job)
        
        
        
        
        
        # Site Catalog
        # create a "local" site
        sc = SiteCatalog()
        local = Site("local", arch=Arch.X86_64, os_type=OS.LINUX)
        
        #DECEPTION_SCRATCH = os.environ.get("TMP_DIR")
        DECEPTION_SCRATCH = "/scratch/tang584"
        OUTPUT_DIR = "/qfs/projects/oddite/tang584/casa_nowcast_runs"

        # create and add a shared scratch and local storage directories to the site "local"
        local_shared_scratch_dir = Directory(Directory.SHARED_SCRATCH, path=DECEPTION_SCRATCH)\
                                    .add_file_servers(FileServer(f"file://{DECEPTION_SCRATCH}", Operation.ALL))
        local_local_storage_dir = Directory(Directory.LOCAL_STORAGE, path=OUTPUT_DIR)\
                                    .add_file_servers(FileServer(f"file://{OUTPUT_DIR}", Operation.ALL))
        local.add_directories(local_shared_scratch_dir, local_local_storage_dir)
        # add all the sites to the site catalog object
        sc.add_sites(local)



        # rc = ReplicaCatalog().add_replica("./replicas.yml")
        # tc = TransformationCatalog().add_transformations("transformations.yml")
        
        
        wf.add_site_catalog(sc)
        
        # Write the Workflow YAML file
        ymlfile = os.path.join(self.outdir, wf.name+".yml")
        wf.write(ymlfile)
        print(ymlfile)
        
        
        # wf.add_replica_catalog(rc)
        # wf.add_transformation_catalog(tc)
        
        # try:
        #     wf.plan(submit=True)\
        #             .wait()\
        #             .analyze()\
        #             .statistics()
        # except PegasusClientError as e:
        #     print(e)
        

    def generate_workflow(self):
        # Generate dax
        self.generate_dax()

if __name__ == '__main__':
    parser = ArgumentParser(description="CASA Nowcast Workflow")
    parser.add_argument("-f", "--files", metavar="INPUT_FILE", type=str, nargs="+", help="Forecast Filename", required=True)
    parser.add_argument("-o", "--outdir", metavar="OUTPUT_LOCATION", type=str, help="DAX Directory", required=True)

    args = parser.parse_args()
    outdir = os.path.abspath(args.outdir)
    
    if not os.path.isdir(args.outdir):
        os.makedirs(outdir)

    workflow = CASAWorkflow(outdir, args.files)
    workflow.generate_workflow()
