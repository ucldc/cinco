from django.http import HttpResponseForbidden


def user_has_repo_access(func):
    def wrapper(request, *args, **kwargs):
        repo_id = kwargs.get('repository_id', None)
        if request.user.has_repo_access(repo_id):
            return func(request, *args, **kwargs)

        return HttpResponseForbidden("You do not have a role in this repository")

    return wrapper


# def user_has_role(func):
#     def wrapper(request, *args, **kwargs):
#         if request.user.has_repo_access(kwargs.get('repository_id'),
#                                         kwargs.get('role')):
#             return func(request, *args, **kwargs)

#         return HttpResponseForbidden("You do not have a role in this repository")

#     return wrapper
