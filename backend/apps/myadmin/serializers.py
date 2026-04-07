# from rest_framework import serializers

# class PlanFeatureSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PlanFeature
#         fields = '__all__'


# class PlanSerializer(serializers.ModelSerializer):
#     features = PlanFeatureSerializer()

#     class Meta:
#         model = Plan
#         fields = ['id', 'name', 'price', 'features']


from rest_framework import serializers
from .models import *

from rest_framework import serializers
from .models import Plan, PlanFeature

class PlanFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanFeature
        exclude = ['plan']


class PlanSerializer(serializers.ModelSerializer):
    features = PlanFeatureSerializer()

    class Meta:
        model = Plan
        fields = ['id', 'name', 'price', 'features']

    def create(self, validated_data):
        features_data = validated_data.pop('features')

        plan = Plan.objects.create(**validated_data)
        PlanFeature.objects.create(plan=plan, **features_data)

        return plan