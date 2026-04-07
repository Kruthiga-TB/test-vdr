from rest_framework import serializers
from .models import Plan


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            'id',
            'name',
            'price',
            'max_users',
            'storage_gb',
            'projects'
        ]
        read_only_fields = ['price', 'max_users', 'storage_gb', 'projects']




# from rest_framework import serializers
# from .models import *

# from rest_framework import serializers
# from .models import Plan, PlanFeature

# class PlanFeatureSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PlanFeature
#         exclude = ['plan']


# class PlanSerializer(serializers.ModelSerializer):
#     features = PlanFeatureSerializer()

#     class Meta:
#         model = Plan
#         fields = ['id', 'name', 'price', 'features']

#     def create(self, validated_data):
#         features_data = validated_data.pop('features')

#         plan = Plan.objects.create(**validated_data)
#         PlanFeature.objects.create(plan=plan, **features_data)

#         return plan