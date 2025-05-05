# cinco

Install pyenv, and it should automagically use the python version specified in `.python-version`

Tooling is listed in dev-requirements.txt

For the pre-commit-config to work, make sure you're using rbenv, and have set `rbenv global 3.3.6` or higher ruby version. Rubocop pre-commit doesn't respect `rbenv local` or `.ruby-version` files, but does respect `rbenv global`, for some reason.

(The Ruby Version used by arclight is specified in `arclight/.ruby-version`)
