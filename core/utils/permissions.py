def get_user_permissions(user):
    if not user.is_authenticated:
        return []

    # Get permissions from user's groups
    group_permissions = user.groups.values_list('permissions__codename', flat=True)

    # Get permissions directly assigned to the user
    user_permissions = user.user_permissions.values_list('codename', flat=True)

    # Combine and remove duplicates
    permissions = set(group_permissions).union(user_permissions)

    return list(permissions)
