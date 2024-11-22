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
sceptre launch admin/app-servers.yaml
```

> Sceptre must be run from the `infrastructure/cinco` directory, and must not include `config` as part of the stack path. 

You could also launch a "stack group":

```
cd infrastructure/cinco
src env.local
sceptre launch admin
```

Other useful sceptre commands:

```
sceptre --debug generate admin/app-servers.yaml
sceptre --debug validate admin/app-servers.yaml
sceptre --debug launch admin/app-servers.yaml --disable-rollback
sceptre --debug delete admin/app-servers.yaml
```

- `generate` outputs the CloudFormation template - for example, the `ecs-webapp.j2` template is a jinja template and the `admin/app-servers.yaml` config provides some `sceptre_user_data` that is resolved at `generate` time to produce the CloudFormation template. 
- `validate` validates the CloudFormation template against AWS and corresponds to the `validate-template` command in the aws cloudformation cli - requires credentials. 
- `launch` creates or updates a CloudFormation stack using the parameters provided in the config, for example, `launch admin/app-servers.yaml` updates the cinco-admin-app-servers stack, using the template configured in app-servers.yaml (doing any `generate` step required, if the template is not a straight yaml template), and the parameters configured in app-servers.yaml. 
- `delete` destroys a CloudFormation stack. 

> When updating stacks, be aware that some resource properties are immutable and, if updated, will require deleting and recreating the resource entirely. Property immutablity coupled with resource deletion protection can create unexpected results.

> Sceptre resolvers can resolve parameter values like "!stack_output admin/db.yaml::RDSHostName", but "launching" a stack with a parameter value that references another stack will trigger updating that stack as well (and any stacks that stack may reference)! Be careful about lingering working branch changes.

Templates are in `infrastructure/cinco/templates` directory. The ecs-webapp.j2 template is diagramed here: 

![Infrastructure Diagram for ecs-webapp template](infrastructure/cinco/ecs-webapp-template.png)