from rest_framework.response import Response
from rest_framework import serializers, status

from business.models import Business
from usermodel.serializers import UserSerializer
from .models import *

class RealUserProfileSerializer(serializers.ModelSerializer):
    role = serializers.CharField(required=False)
    user = serializers.CharField(required=False)

    class Meta:
        model = RealUserProfile
        fields = '__all__'

    def create(self, validated_data):
        user = self.context['request'].user
        role = 'customer'
        if RealUserProfile.objects.filter(user=user):
            raise serializers.ValidationError('کاربر قبلا پروفایل ثبت کرده')
        else:
            instance = RealUserProfile.objects.create(user=user, role=role, **validated_data)
            return instance

class AgentCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentCompany
        fields = '__all__'

    def update(self, instance, validated_data):
        user = self.context['request'].user
        profile_id = self.context['view'].kwargs.get('id')
        agent_user_instance = AgentCompany.objects.filter(id=profile_id, agent__user=user).first()
        agent_admin_instance = AgentCompany.objects.filter(id=profile_id, agent__user_admin=user).first()

        if agent_user_instance or agent_admin_instance:
            agent_instance = agent_user_instance or agent_admin_instance
            for field in agent_instance._meta.fields:
                field_name = field.name
                setattr(agent_instance, field_name,
                        validated_data.get(field_name, getattr(agent_instance, field_name)))
                agent_instance.save()
            return agent_instance

        else:
            raise serializers.ValidationError('نماینده یافت نشد')



class CustomPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def to_representation(self, value):
        return {'id': value.pk, 'username': str(value)}
class LegalUserProfileSerializer(serializers.ModelSerializer):
    role = serializers.CharField(required=False)
    user_admin = serializers.CharField(required=False)
    agent = CustomPrimaryKeyRelatedField(required=False, queryset=AgentCompany.objects.all(), many=True)
    user = CustomPrimaryKeyRelatedField(required=False, queryset=CustomUser.objects.all(), many=True)

    class Meta:
        model = LegalUserProfile
        fields = '__all__'

    def create(self, validated_data):
        requesting_user = self.context['request'].user
        default_role = 'customer'
        users_data = validated_data.pop('user', None)
        agents_data = validated_data.pop('agent', None)
        agent_ids = []
        legal_user_profile_instance = LegalUserProfile.objects.create(
            user_admin=requesting_user,
            role=default_role,
            **validated_data
        )
        real = RealUserProfile.objects.filter(user=requesting_user).first()
        if real:
            businesses = Business.objects.filter(real_profile=real)
            if businesses:
                for business in businesses:
                    business.legal_profile = legal_user_profile_instance
                    business.real_profile = None
                    business.save()
        if agents_data:
            for agent_data in agents_data:
                if agent_data in AgentCompany.objects.filter(company_name=validated_data['company_name']).all():
                    agent_ids.append(agent_data.id)
                else:
                    raise serializers.ValidationError(f'نماینده {agent_data} برای شرکتی با این نام یافت نشد')

            legal_user_profile_instance.agent.set(agent_ids)
        if users_data:
            legal_user_profile_instance.user.set(users_data)


        return legal_user_profile_instance


    def update(self, instance, validated_data):
        user = self.context['request'].user
        profile_id = self.context['view'].kwargs.get('id')

        user_admin_profile = LegalUserProfile.objects.filter(user_admin=user, id=profile_id).first()
        user_profile = LegalUserProfile.objects.filter(user=user, id=profile_id).first()

        if user_admin_profile or user_profile:
            profile_instance = user_admin_profile or user_profile
            for field in profile_instance._meta.fields:
                field_name = field.name
                setattr(profile_instance, field_name,
                        validated_data.get(field_name, getattr(profile_instance, field_name)))

            #update user data it seprate because of manytomany field
            users_data = validated_data.get('user', None)
            if users_data is not None:
                profile_instance.user.set(users_data)

            profile_instance.save()

            return profile_instance
        else:
            raise serializers.ValidationError('ویرایش قابل انجام نیست')


