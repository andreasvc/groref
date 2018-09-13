Deterministic Rule-Based Coreference Resolution for Dutch
=========================================================

To evaluate the system on development data:

	$ python3 run_pipeline.py clinDevData/

Alpino should be used first, see `alpino.py`.


To run the system on a directory of Alpino parse trees:

	$ python3 coreference_resolution.py parses/ output.coref


References
----------
This is a fork of https://bitbucket.org/robvanderg/groref

Which in turn is based on Stanford's Multi-Pass Sieve Coreference Resolution System:

Heeyoung Lee, Angel Chang, Yves Peirsman, Nathanael Chambers, Mihai
Surdeanu, and Dan Jurafsky. Deterministic coreference resolution based
on entity-centric, precision-ranked rules. Computational Linguistics, 39
(4):885–916, 2013. http://aclweb.org/anthology/J/J13/J13-4004.pdf
