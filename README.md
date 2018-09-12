
This is a fork of https://bitbucket.org/robvanderg/groref

To evaluate the system on development data:

python2 run_pipeline.py clinDevData/

Alpino should be used first, see alpino.py


To run the system on a directory of Alpino parse trees:

python2 coreference_resolution.py parses/ output.coref

