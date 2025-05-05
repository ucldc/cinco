# Django Airflow Client App

A second stab at a Django Airflow Client App (after the Collection Registry).

We often run Airflow DAGs parameterized by things - Finding Aids (for Cinco), Collections (for Calisphere) - and those related models (used in the job's parameters) are usually managed in a Django app somewhere.

Frequently, we want to run the job from the place where these related models are managed, and we also want to be able to look at information about jobs sorted by their related models: the last successful job for a Finding Aid, the status of a currently running job for a Collection, tracking down the logs for a job run weeks ago for a specific Collection, etc. Airflow's UI is not designed for filtering Dag Runs by their parameters, though.

The Django Airflow Client Application tries to bridge that gap.

## Models

**JobTriggers** are typically ephemeral and record the request and response from the Airflow API when triggering a job.

JobTriggers are deleted as part of the airflow_client app and can be configured using the AIRFLOW_PRESERVE_JOB_TRIGGER setting. When False (the default), a JobTrigger is deleted when a JobRun is created. We need to keep the JobTrigger around until at least this point so we can use it to ask airflow how the job is doing and if it is running.

**JobRuns**

JobRuns defer their lifecycle to the application using them - for Cinco, JobRuns are deleted as part of the findingaids app. When a JobRun is saved, we query for all other JobRuns attached to the same FindingAid, and delete all but the most recent success and the one that was just saved (which most likely will be the same JobRun). Rikolti has a different set of needs regarding the persistence of past JobRuns.

## Notes

Calisphere's Collection Registry's Airflow Client was developed before the Airflow API was supported by MWAA. The Collection Registry uses a MWAA API (as opposed to the Airflow API) to send a CLI command to Airflow. Since we couldn't query the API to get information about Dag Runs, Rikolti's Dag Runs actually publish out data consistently (in the on_success and on_failure callbacks for tasks and dags), and the Collection Registry reads this log and attempts to line everything up with the Dag Runs it knows about (creating a new Dag Run if none exists in the Registry's understanding of runs). This model supports trigger a job both from the Collection Registry and from Airflow, and the job will eventually be represented in both places.

Cinco's Airflow Client makes an assumption that it knows about all the runs, and only queries for runs it already knows about (because it triggered all of them). I think Cinco's JobTrigger model is better, but I actually think Rikolti's JobRun model is better.
