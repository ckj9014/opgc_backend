import operator
from functools import reduce

from chunkator import chunkator
from django.db.models import Q

from apps.githubs.models import BlockUser, Repository, GithubUser
from core.services.repository_service import AUTO_COMMIT_REPO_NAME_REGEX


def run():
    clauses = (Q(name__icontains=p) for p in AUTO_COMMIT_REPO_NAME_REGEX)
    query = reduce(operator.or_, clauses)
    repositories = Repository.objects.filter(query).prefetch_related('github_user')

    blacklist = set()
    for repo in chunkator(repositories, 1000):
        blacklist.add(repo.github_user.username)

    print(f'블랙리스트: {len(blacklist)}명\n{blacklist}')

    answer = input("Are you sure you want to delete it?(y or n): ")
    if answer == 'y':
        for username in blacklist:
            try:
                github_user = GithubUser.objects.get(username=username)
                github_user.delete()
                BlockUser.objects.get_or_create(username=username)
            except:
                continue
