# views.py
from rest_framework import generics
from .models import AgeGroup, Theory, Assessment
from .serializers import AgeGroupSerializer, TheorySerializer, AssessmentSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Assessment
from .utils.ai_assessment import generate_question, evaluate_answer

class AgeGroupListCreateAPIView(generics.ListCreateAPIView):
    queryset = AgeGroup.objects.all()
    serializer_class = AgeGroupSerializer

class AgeGroupRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AgeGroup.objects.all()
    serializer_class = AgeGroupSerializer

class TheoryListCreateAPIView(generics.ListCreateAPIView):
    queryset = Theory.objects.all()
    serializer_class = TheorySerializer

class TheoryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Theory.objects.all()
    serializer_class = TheorySerializer

class AssessmentListCreateView(generics.ListCreateAPIView):
    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer

class AssessmentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer



# In-memory cache (or use Redis/db for persistence)
SESSION_STORE = {}

class AIQuestionView(APIView):
    def post(self, request, assessment_id):
        answer = request.data.get("answer", None)

        try:
            assessment = Assessment.objects.get(id=assessment_id)
        except Assessment.DoesNotExist:
            return Response({"error": "Assessment not found"}, status=404)

        session = SESSION_STORE.get(assessment_id, {"qas": [], "completed": False})

        if session["completed"]:
            return Response({"message": "Assessment completed"}, status=200)

        previous_qas = "\n".join([f"Q: {qa['question']}\nA: {qa['answer']}" for qa in session["qas"]])

        # Evaluate previous answer if it exists
        if answer and session["qas"]:
            last_q = session["qas"][-1]['question']
            evaluation = evaluate_answer(last_q, answer, assessment.theory.content)
            session["qas"][-1]["answer"] = answer
            session["qas"][-1]["evaluation"] = evaluation
        elif answer and not session["qas"]:
            return Response({"error": "No question asked yet"}, status=400)

        # Stop after 10 questions
        if len(session["qas"]) >= 10:
            session["completed"] = True
            SESSION_STORE[assessment_id] = session
            return Response({"message": "Assessment completed", "report": session["qas"]})

        # Generate next question
        new_q = generate_question(assessment.theory.content, previous_qas)
        session["qas"].append({"question": new_q, "answer": None, "evaluation": None})
        SESSION_STORE[assessment_id] = session

        return Response({
            "question": new_q,
            "question_number": len(session["qas"]),
        })

