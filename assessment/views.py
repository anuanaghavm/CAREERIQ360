# views.py
from rest_framework import generics
from .models import Test, Theory, Assessment
from .serializers import TestSerializer, TheorySerializer, AssessmentSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Assessment
from .utils.ai_assessment import generate_question, evaluate_answer,generate_ai_report

class TestListCreateAPIView(generics.ListCreateAPIView):
    queryset = Test.objects.all()
    serializer_class = TestSerializer

class TestRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Test.objects.all()
    serializer_class = TestSerializer

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


class AgeGroupTestTheoryAPIView(APIView):
    def get(self, request):
        age_group = request.query_params.get('age_group')
        if not age_group:
            return Response({'error': 'age_group parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        assessments = Assessment.objects.filter(age_group=age_group)
        test_ids = assessments.values_list('test_id', flat=True).distinct()
        theory_ids = assessments.values_list('theory_id', flat=True).distinct()

        tests = Test.objects.filter(id__in=test_ids)
        theories = Theory.objects.filter(id__in=theory_ids)

        test_serializer = TestSerializer(tests, many=True)
        theory_serializer = TheorySerializer(theories, many=True)

        return Response({
            'age_group': age_group,
            'tests': test_serializer.data,
            'theories': theory_serializer.data
        })


# In-memory cache (or use Redis/db for persistence)
# SESSION_STORE = {}

# class AIQuestionView(APIView):
#     def post(self, request, assessment_id):
#         answer = request.data.get("answer", None)

#         try:
#             assessment = Assessment.objects.select_related("theory", "age_group").get(id=assessment_id)
#         except Assessment.DoesNotExist:
#             return Response({"error": "Assessment not found"}, status=404)

#         session = SESSION_STORE.get(assessment_id, {"qas": [], "completed": False})

#         if session["completed"]:
#             return Response({"message": "Assessment completed", "report": session["qas"]}, status=200)

#         previous_qas = "\n".join(
#             [f"Q: {qa['question']}\nA: {qa['answer']}" for qa in session["qas"] if qa.get("answer")]
#         )

#         # Evaluate last answer
#         if answer and session["qas"]:
#             last_q = session["qas"][-1]["question"]
#             evaluation = evaluate_answer(last_q, answer, assessment.theory.content)
#             session["qas"][-1]["answer"] = answer
#             session["qas"][-1]["evaluation"] = evaluation
#         elif answer and not session["qas"]:
#             return Response({"error": "No question asked yet"}, status=400)

#         # End after 10 questions
#         if len(session["qas"]) >= 10:
#             session["completed"] = True
#             SESSION_STORE[assessment_id] = session
#             return Response({"message": "Assessment completed", "report": session["qas"]}, status=200)

#         # ✅ Generate new question (pass all required args)
#         question_data = generate_question(
#             theory_text=assessment.theory.content,
#             age_group=assessment.age_group.name,
#             assessment_title=assessment.test_name,
#             previous_qas=previous_qas
#         )

#         session["qas"].append({
#             "question": question_data["question"],
#             "options": question_data["options"],
#             "answer": None,
#             "evaluation": None
#         })

#         SESSION_STORE[assessment_id] = session

#         return Response({
#             "question": question_data["question"],
#             "options": question_data["options"],
#             "question_number": len(session["qas"])
#         })

SESSION_STORE = {}
QUESTION_ID_COUNTER = {}
MAX_QUESTIONS = 2

class AIQuestionView(APIView):
    def post(self, request, assessment_id):
        answer = request.data.get("answer")
        question_id = request.data.get("question_id")

        try:
            assessment = Assessment.objects.get(id=assessment_id)
        except Assessment.DoesNotExist:
            return Response({"error": "Assessment not found"}, status=404)

        session = SESSION_STORE.get(assessment_id, {"qas": [], "completed": False})
        question_list = session["qas"]

        # Handle answer submission
        if answer and question_id:
            for item in question_list:
                if item["question_id"] == question_id:
                    if item["answer"] is not None:
                        return Response({"error": "Already answered"}, status=400)
                    selected_text = item["options"].get(answer.lower())
                    if not selected_text:
                        return Response({"error": "Invalid option."}, status=400)

                    evaluation = evaluate_answer(item["question"], selected_text, assessment.theory.content)
                    item["answer"] = selected_text
                    item["evaluation"] = evaluation
                    break
            else:
                return Response({"error": "Question ID not found."}, status=404)

        # If all answered, mark as completed
        if all(qa["answer"] for qa in question_list) and len(question_list) >= MAX_QUESTIONS:
            session["completed"] = True
            SESSION_STORE[assessment_id] = session
            return Response({"message": "Assessment completed."})

        # Prevent creating more than max questions
        if len(question_list) >= MAX_QUESTIONS:
            return Response({"message": "Maximum questions reached. Submit all answers to get report."})

        # Generate next question
        previous_qas = "\n".join([
            f"Q: {qa['question']}\nA: {qa['answer']}" for qa in question_list if qa["answer"]
        ])
        question_data = generate_question(assessment.theory.content, previous_qas, len(question_list))
        qid = QUESTION_ID_COUNTER.get(assessment_id, 1)
        QUESTION_ID_COUNTER[assessment_id] = qid + 1

        question_entry = {
            "question_id": qid,
            "question": question_data["question"],
            "options": question_data["options"],
            "answer": None,
            "evaluation": None
        }

        session["qas"].append(question_entry)
        SESSION_STORE[assessment_id] = session

        return Response({
            "question_id": qid,
            "question": question_data["question"],
            "options": question_data["options"],
            "question_number": len(session["qas"]),
        })

class AIReportView(APIView):
    def get(self, request, assessment_id):
        session = SESSION_STORE.get(assessment_id)
        if not session or not session.get("completed"):
            return Response({"error": "Incomplete assessment"}, status=400)

        report = generate_ai_report(session["qas"])
        return Response({"report": report})