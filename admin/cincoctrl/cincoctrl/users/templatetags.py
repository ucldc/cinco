from django import template

register = template.Library()


@register.simple_tag
def user_has_repo_access(user, repo_id, *args, **kwargs):
    return user.has_repo_access(repo_id)


@register.simple_tag
def user_has_role(user, repo_id, role, *args, **kwargs):
    return user.has_role(repo_id, role)
