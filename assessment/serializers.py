# serializers.py
from rest_framework import serializers
from .models import AgeGroup, Theory, Assessment

class AgeGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgeGroup
        fields = '__all__'

class TheorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Theory
        fields = '__all__'

class AssessmentSerializer(serializers.ModelSerializer):
    age_group = AgeGroupSerializer(read_only=True)
    theory = TheorySerializer(read_only=True)
    age_group_id = serializers.PrimaryKeyRelatedField(queryset=AgeGroup.objects.all(), source='age_group', write_only=True)
    theory_id = serializers.PrimaryKeyRelatedField(queryset=Theory.objects.all(), source='theory', write_only=True)

    class Meta:
        model = Assessment
        fields = ['id', 'test_name', 'age_group', 'age_group_id', 'theory', 'theory_id', 'created_at']
