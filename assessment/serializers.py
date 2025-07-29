# serializers.py
from rest_framework import serializers
from .models import Test, Theory, Assessment

class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = '__all__'

class TheorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Theory
        fields = '__all__'

class AssessmentSerializer(serializers.ModelSerializer):
    test = TestSerializer(read_only=True)
    theory = TheorySerializer(read_only=True)
    test_id = serializers.PrimaryKeyRelatedField(queryset=Test.objects.all(), source='test', write_only=True)
    theory_id = serializers.PrimaryKeyRelatedField(queryset=Theory.objects.all(), source='theory', write_only=True)

    class Meta:
        model = Assessment
        fields = ['id', 'age_group', 'test', 'test_id', 'theory', 'theory_id', 'created_at']
