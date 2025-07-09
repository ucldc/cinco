## Infrastructure

The Infrastructure directory contains the "cinco" sceptre project and makes use of two tooling libraries listed in dev-requirements.txt:

- sceptre: provides a wrapper around the `aws cloudformation` cli and an added layer of jinja templating ontop of the cloudformation templating. Jinja templating allows for more complex templating options like if statements and for loops wrapped around resources and their properties. More information here: https://docs.sceptre-project.org/latest/
- cfn-lint: a handy linter I use in my vs code setup. I'd like to get this integrated into the pre-commit hook.

### Using Sceptre

You'll need some environment variables: `cp infrastructure/cinco/env.example infrastructure/cinco/env.local` and modify accordingly.

#### Stack Config

Stacks are described in the `config` directory. A stack is a template that has been configured in a specific way. Sceptre commands are typically run against a specific stack.

To create or update all stacks in the cinco infrastructure, navigate into the sceptre project, source the local environment, and run `sceptre launch`:
```
cd infrastructure/cinco
src env.local
sceptre launch
```

To create or update only a single stack or stack group (this is a sceptre-ism, not a cloudformation grouping) in the cinco infrastructure, specify which cloudformation stack in the `infrastructure/cinco/config` directory you'd like to launch, relative to the `config` directory, for example:

```
cd infrastructure/cinco
src env.local
sceptre launch ctrl/ctrl.yaml
```

> Sceptre must be run from the `infrastructure/cinco` directory, and must not include `config` as part of the stack path.

You could also launch a "stack group":

```
cd infrastructure/cinco
src env.local
sceptre launch ctrl
```

Other useful sceptre commands:

```
sceptre --debug generate ctrl/ctrl.yaml
sceptre --debug validate ctrl/ctrl.yaml
sceptre --debug launch ctrl/ctrl.yaml --disable-rollback
sceptre --debug delete ctrl/ctrl.yaml
```

- `generate` outputs the CloudFormation template - for example, the `ecs-webapp.j2` template is a jinja template and the `ctrl/ctrl.yaml` config provides some `sceptre_user_data` that is resolved at `generate` time to produce the CloudFormation template.
- `validate` validates the CloudFormation template against AWS and corresponds to the `validate-template` command in the aws cloudformation cli - requires credentials.
- `launch` creates or updates a CloudFormation stack using the parameters provided in the config, for example, `launch ctrl/ctrl.yaml` updates the cinco-ctrl-ctrl stack, using the template configured in ctrl.yaml (doing any `generate` step required, if the template is not a straight yaml template), and the parameters configured in ctrl.yaml.
- `delete` destroys a CloudFormation stack.

> When updating stacks, be aware that some resource properties are immutable and, if updated, will require deleting and recreating the resource entirely. Property immutablity coupled with resource deletion protection can create unexpected results.

> Sceptre resolvers can resolve parameter values like "!stack_output cincoctrl/db.yaml::RDSHostName", but "launching" a stack with a parameter value that references another stack will trigger updating that stack as well (and any stacks that stack may reference)! Be careful about lingering working branch changes.

Templates are in `infrastructure/cinco/templates` directory. The ecs-webapp.j2 template is diagramed here:

![Infrastructure Diagram for ecs-webapp template](infrastructure/cinco/ecs-webapp-template.png)

### Notes on Solr setup

Using Solr standalone instead of Solr Cloud saves us the hassle of running ZooKeeper; however, the fact that Solr standalone is designed to be deployed as a pet rather than as cattle makes makes deployment in ECS a bit of a hassle. The big gotcha with running Solr standalone: spinning up a 2nd instance of the same index that writes to the same disk as the 1st will cause Solr to throw an index directory locking error. *A given Solr ECS service can run one and only one copy of the ECS task at a time.* This means that we cannot do blue-green/rolling deploys, and instead must always stop the existing container before starting a new one; replacing a Solr application/container version will always cause downtime.

#### Index Replication

We are using Solr [index replication](https://solr.apache.org/guide/solr/latest/deployment-guide/user-managed-index-replication.html).

We currently have 3 solr services running, e.g. in stage:

- cinco-solr-stage-service - the solr leader instance
- cinco-solr-follower-stage-1-service - the first follower instance
- cinco-solr-follower-stage-2-service - the second follower instance

The leader instance functions as the "writer" instance. Indexing work is done here. The follower instances are configured to be kept in sync with the leader, and they function as "reader" instances. The arclight application gets its data from the followers. The only difference between the first and second follower containers is that they write their data to different disk spaces.

The solr containers are configured as leader or follower (or neither) on startup via the `arclight/solr/solr-replication-config.py` script. This is run as part of the docker entrypoint script: `arclight/solr/cinco-docker-entrypoint.sh`.

#### Configuring allowUrls

When using index replication, Solr requires that you either add the leader URL to `allowUrls` in `solr.xml`, or set `-Dsolr.disable.allowUrls=true` to disable URL allow-list checks.

The first option ended up being the least onerous. The modified `solr.xml` file is copied into the Docker image during build (see `Dockerfile.solr`).

We are using ECS ServiceConnect for communication between the leader and follower containers, which gives us a stable leader URL.

#### Updating Solr

We have deployed each of the 2 solr follower containers to its own ECS service. This allows us to update them individually and avoid both being down at the same time. TODO: automate this using CodePipeline.

Unfortunately, there can by definition be only one Solr leader. This means that any updates necessitating task replacement will cause downtime.

#### Load balancers

The 2 follower containers are targets of the same target group on the same load balancer. This load balancer is created as part of the `cinco-stage-solr-solr-follower-1` CloudFormation stack. Its details are then passed in to the `solr-follower-2` template as parameters. Somewhat unintuitively, then, the `cinco-solr-follower-1-stage-alb` alb serves as the load balancer for both followers.

The solr leader is fronted by its own load balancer.
