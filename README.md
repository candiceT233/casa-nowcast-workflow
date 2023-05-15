# casa-nowcast-workflow

## Old DAX3 API
```
pip install pegasus-wms.dax

python daxgen.py -f input/mrtV2_config.txt jobs_schemas/
./plan.sh jobs_schemas/casa_nowcast-wf-20230515T192620Z.dax
```

## Pegasus.api
DAX3 tp Pegasus for 5.0.+
https://pegasus.isi.edu/documentation/user-guide/migration.html?highlight=dax#moving-from-dax3-to-pegasus-api
```
python workflow_generator.py -f input/mrtV2_config.txt -o jobs_schemas/
```

## Convert to shell
```
pegasus-sc-converter -i sites.xml -o sites.yml
pegasus-tc-converter -i tc.txt -I Text -O YAML -o transformations.yml
pegasus-rc-converter -I File -O YAML -i rc.txt -o default_replicas.yml

sed "s|\${PWD}|$(pwd)|g" default_replicas.yml > replicas.yml

python dag_to_shell.py -w jobs_schemas/casa_nowcast-wf.yml -r replicas.yml -t transformations.yml  -o shell_script/casa_nowcast-wf.sh
```

```
python dag_to_shell.py --workflow_yml jobs_schemas/casa_nowcast-wf.yml \
                        --replica_yml replicas.yml \
                        --transformation_yml transformations.yml \
                        --output casa_nowcast-wf.sh
```

Make sure to `mkdir /qfs/projects/oddite/$USER/casa_nowcast_runs` for running the shell script