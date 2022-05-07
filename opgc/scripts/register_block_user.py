from apps.githubs.models import BlockUser


def run():
    username = input("input block username: ")
    answer = input("Are you sure you want to block this user?(y or n): ")

    if answer == 'y':
        BlockUser.objects.get_or_create(username=username)
