# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from rest_framework import viewsets, serializers, status, filters
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from physical.models import Environment, Pool
from account.models import Team
from api.team import TeamSerializer
from system.models import Configuration
from django.core.exceptions import ValidationError


class PoolSerializer(serializers.HyperlinkedModelSerializer):
    teams = TeamSerializer(many=True, read_only=True)

    class Meta:
        model = Pool
        fields = (
            'id', 'name', 'environment', 'teams'
        )


class PoolAPI(viewsets.ModelViewSet):

    model = Pool
    serializer_class = PoolSerializer
    permission_classes = []
    authentication_classes = []
    filter_backends = (filters.OrderingFilter,)
    filter_fields = (
        "name",
        "environment",
        "teams__name"
    )

    def validate_required_fields(self, data):
        required_fields = (
            "cluster_name",
            "cluster_id",
            "cluster_endpoint",
            "rancher_endpoint",
            "rancher_token",
            "dbaas_token",
            "teams",
        )
        for field in required_fields:
            if not data.get(field, ''):
                error = "{} is required".format(field)
                raise ValidationError(error)

    def update_environment(self, data):
        env_name = data.get('environment', '')
        k8s_envs = Environment.k8s_envs()
        env = Environment.objects.get(
            name=env_name if env_name else k8s_envs[0]
        )
        data['environment'] = env

    def validate_and_get_teams(self, team_names):
        teams = []
        for team_name in team_names:
            team = Team.objects.filter(name=team_name).first()
            if not team:
                error = 'Team {} not found'.format(team_name)
                raise ValidationError(error)
            teams.append(team)
        return teams

    def validade_toke(self, teams, token):
        for team in teams:
            if token == team.token:
                return
        error = 'Token {} is not valid.'.format(token)
        raise ValidationError(error)

    def create(self, request):
        serializer = self.get_serializer(
            data=request.DATA, files=request.FILES)
        data = serializer.init_data

        self.validate_required_fields(data)
        self.update_environment(data)

        team_names = data.pop('teams')
        teams = self.validate_and_get_teams(team_names)

        dbaas_token = data.get('dbaas_token')
        self.validade_toke(teams, dbaas_token)

        pool_name = "{}:{}".format(
            data.get('cluster_name'),
            data.get('cluster_id')
        )
        data['name'] = pool_name

        pool, created = self.model.objects.get_or_create(
            name=pool_name,
            defaults=data
        )
        if not created:
            for attr, value in data.items():
                setattr(pool, attr, value)
            pool.save()

        pool.teams.clear()
        for team in teams:
            pool.teams.add(team)

        headers = self.get_success_headers(data)
        return Response(
            {"pool": pool.id}, status=status.HTTP_201_CREATED,
            headers=headers
        )

    # def destroy(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     UserMiddleware.set_current_user(request.user)

    #     if instance.is_in_quarantine or instance.is_protected:
    #         return Response(status=status.HTTP_401_UNAUTHORIZED)

    #     instance.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)
