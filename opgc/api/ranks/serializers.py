
from rest_framework import serializers

from apps.githubs.models import GithubUser
from apps.ranks.models import UserRank


class RankUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = GithubUser
        fields = ('id', 'username', 'avatar_url')


class RankSerializer(serializers.ModelSerializer):
    github_user = RankUserSerializer()

    class Meta:
        model = UserRank
        fields = ('id', 'ranking', 'score', 'github_user')


class TierSerializer(serializers.ModelSerializer):
    tier = serializers.CharField(source='get_tier_display')
    continuous_commit_day = serializers.IntegerField(source='total_score')  # todo: 프론트 api 변경전 임시로

    class Meta:
        model = GithubUser
        fields = ('id', 'username', 'name', 'avatar_url', 'tier', 'user_rank', 'previous_user_rank', 'company', 'bio',
                  'continuous_commit_day', 'total_score', 'following', 'followers', 'total_contribution',)
