# # views.py
# from rest_framework import generics
# from .models import Test, Theory, Assessment
# from .serializers import TestSerializer, TheorySerializer, AssessmentSerializer
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from .models import Assessment
# from .utils.ai_assessment import get_tests_by_section,get_all_sections,generate_questions_for_test
# from django.utils import timezone
# import json
# from rest_framework.decorators import api_view

# class TestListCreateAPIView(generics.ListCreateAPIView):
#     queryset = Test.objects.all()
#     serializer_class = TestSerializer

# class TestRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Test.objects.all()
#     serializer_class = TestSerializer

# class TheoryListCreateAPIView(generics.ListCreateAPIView):
#     queryset = Theory.objects.all()
#     serializer_class = TheorySerializer

# class TheoryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Theory.objects.all()
#     serializer_class = TheorySerializer

# class AssessmentListCreateView(generics.ListCreateAPIView):
#     queryset = Assessment.objects.all()
#     serializer_class = AssessmentSerializer

# class AssessmentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Assessment.objects.all()
#     serializer_class = AssessmentSerializer


# class AgeGroupTestTheoryAPIView(APIView):
#     def get(self, request):
#         age_group = request.query_params.get('age_group')
#         if not age_group:
#             return Response({'error': 'age_group parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
#         assessments = Assessment.objects.filter(age_group=age_group)
#         test_ids = assessments.values_list('test_id', flat=True).distinct()
#         theory_ids = assessments.values_list('theory_id', flat=True).distinct()

#         tests = Test.objects.filter(id__in=test_ids)
#         theories = Theory.objects.filter(id__in=theory_ids)

#         test_serializer = TestSerializer(tests, many=True)
#         theory_serializer = TheorySerializer(theories, many=True)

#         return Response({
#             'age_group': age_group,
#             'tests': test_serializer.data,
#             'theories': theory_serializer.data
#         })


# SESSION_STORE = {}
# QUESTION_ID_COUNTER = {}
# MAX_QUESTIONS = 3

# class AIQuestionView(APIView):
#     """
#     Generate questions one by one and collect answers
#     """
#     def post(self, request, assessment_id):
#         answer = request.data.get("answer")
#         question_id = request.data.get("question_id")

#         try:
#             assessment = Assessment.objects.select_related("theory", "test").get(id=assessment_id)
#         except Assessment.DoesNotExist:
#             return Response({"error": "Assessment not found"}, status=404)

#         session = SESSION_STORE.get(assessment_id, {
#             "qas": [], 
#             "completed": False,
#             "started_at": timezone.now().isoformat(),
#             "assessment_info": {
#                 "age_group": assessment.age_group,
#                 "test_name": assessment.test.name,
#                 "test_description": assessment.test.description,  # <- Ensure this is added
#                 "theory_content": assessment.theory.content
#             }

#         })
#         question_list = session["qas"]

#         # Handle answer submission
#         if answer and question_id:
#             for item in question_list:
#                 if item["question_id"] == question_id:
#                     if item["answer"] is not None:
#                         return Response({"error": "Already answered"}, status=400)
                    
#                     selected_text = item["options"].get(answer.lower())
#                     if not selected_text:
#                         return Response({"error": "Invalid option."}, status=400)

#                     # Evaluate the answer
#                     evaluation = evaluate_answer(
#                         question=item["question"],
#                         answer_text=selected_text,
#                         theory_text=assessment.theory.content,
#                         test_name=assessment.test.name,
#                         test_description=assessment.test.description,
#                         theory_id=assessment.theory.id
#                     )
                    
#                     item["answer"] = selected_text
#                     item["selected_option"] = answer.upper()
#                     item["evaluation"] = evaluation
#                     item["answered_at"] = timezone.now().isoformat()
#                     break
#             else:
#                 return Response({"error": "Question ID not found."}, status=404)

#         # Check if assessment is completed
#         answered_questions = [qa for qa in question_list if qa.get("answer")]
        
#         if len(answered_questions) >= MAX_QUESTIONS:
#             session["completed"] = True
#             session["completed_at"] = timezone.now().isoformat()
#             SESSION_STORE[assessment_id] = session
            
#             return Response({
#                 "message": "Assessment completed successfully!",
#                 "total_questions": len(question_list),
#                 "answered_questions": len(answered_questions),
#                 "completion_rate": f"{(len(answered_questions)/len(question_list)*100):.1f}%",
#                 "next_step": "Get your comprehensive report at /age-group/reports/"
#             })

#         # Generate next question if not completed
#         if len(question_list) < MAX_QUESTIONS:
#             previous_qas = "\n".join([
#                 f"Q: {qa['question']}\nA: {qa['answer']}" 
#                 for qa in question_list if qa.get("answer")
#             ])
            
#             question_data = generate_question(
#                 theory_text=assessment.theory.content,
#                 test_name=assessment.test.name,
#                 test_description=assessment.test.description,
#                 previous_qas=previous_qas,
#                 question_count=len(question_list),
#                 theory_id=assessment.theory.id
#             )



#             qid = QUESTION_ID_COUNTER.get(assessment_id, 1)
#             QUESTION_ID_COUNTER[assessment_id] = qid + 1

#             question_entry = {
#                 "question_id": qid,
#                 "question": question_data["question"],
#                 "options": question_data["options"],
#                 "answer": None,
#                 "selected_option": None,
#                 "evaluation": None,
#                 "generated_at": timezone.now().isoformat()
#             }

#             session["qas"].append(question_entry)
#             SESSION_STORE[assessment_id] = session

#             return Response({
#                 "question_id": qid,
#                 "question": question_data["question"],
#                 "options": question_data["options"],
#                 "question_number": len(session["qas"]),
#                 "total_questions": MAX_QUESTIONS,
#                 "progress": f"{len(session['qas'])}/{MAX_QUESTIONS}"
#             })

#         return Response({
#             "message": "Please complete all current questions before proceeding.",
#             "answered": len(answered_questions),
#             "remaining": len(question_list) - len(answered_questions)
#         })


# class AgeGroupReportAPIView(APIView):
#     def get(self, request):
#         age_group = request.query_params.get("age_group")
#         if not age_group:
#             return Response({"error": "Missing age_group"}, status=status.HTTP_400_BAD_REQUEST)

#         # Get all assessments for this age group
#         assessments = Assessment.objects.filter(age_group=age_group)

#         # Get all unique tests (should be 5 for report generation)
#         completed_assessments = [a for a in assessments if SESSION_STORE.get(a.id, {}).get("completed")]
#         incomplete_count = len(assessments) - len(completed_assessments)

#         if incomplete_count > 0:
#             return Response({
#                 "age_group": age_group,
#                 "status": "incomplete",
#                 "message": f"{len(completed_assessments)} out of {len(assessments)} assessments completed. {incomplete_count} remaining."
#             }, status=400)

#         # Generate a final report by combining all evaluations
#         all_evaluations = []
#         for assessment in completed_assessments:
#             session = SESSION_STORE.get(assessment.id)
#             if session:
#                 qas = session.get("qas", [])
#                 evaluations = [qa.get("evaluation") for qa in qas if qa.get("evaluation")]
#                 all_evaluations.extend(evaluations)

#         # Combine and analyze all evaluations using GPT
#         report_data = generate_behavior_report_from_evaluations(all_evaluations)

#         return Response({
#             "age_group": age_group,
#             "status": "complete",
#             "report": report_data
#         })

# class IndividualAssessmentReportAPIView(APIView):
#     def get(self, request, assessment_id):
#         session = SESSION_STORE.get(assessment_id)
#         if not session:
#             return Response({"error": "Session not found for this assessment."}, status=404)

#         if not session.get("completed"):
#             return Response({"error": "Assessment not yet completed."}, status=400)

#         qas = session.get("qas", [])
#         test_name = session["assessment_info"].get("test_name")
#         test_description = session["assessment_info"].get("test_description") 
#         theory_content = session["assessment_info"].get("theory_content")

#         report_paragraph = generate_detailed_assessment_report(
#             test_name=test_name,
#             theory_description=theory_content,
#             test_description=test_description,
#             qas=qas
#         )

#         return Response({
#             "assessment_id": assessment_id,
#             "test_name": test_name,
#             "theory_summary": theory_content[:500],  # optional short preview
#             "questions_answered": len([qa for qa in qas if qa.get("answer")]),
#             "report": report_paragraph
#         })

# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .utils.ai_assessment import generate_questions, evaluate_answers, STATIC_TESTS,generate_detailed_assessment_report

SESSION_STORE = {}
MAX_QUESTIONS = 30

class StaticAIQuestionBatchView(APIView):
    def post(self, request):
        test_name = request.data.get("test_name")
        section_name = request.data.get("section_name", "Middle School(13-15)")  # NEW!

        if test_name not in STATIC_TESTS:
            return Response({"error": f"Invalid test name: {test_name}"}, status=400)

        session_key = f"{request.session.session_key}-{test_name}-{section_name}"
        session = {
            "qas": [],
            "completed": False,
            "started_at": timezone.now().isoformat(),
            "section": section_name,
        }

        qas = generate_questions(test_name, section_name=section_name, total=MAX_QUESTIONS)

        for i, qa in enumerate(qas):
            qa["question_id"] = i + 1
            qa["answer"] = None
            qa["selected_option"] = None
            qa["evaluation"] = None
            qa["generated_at"] = timezone.now().isoformat()

        session["qas"] = qas
        SESSION_STORE[session_key] = session

        return Response({
            "test_name": test_name,
            "section": section_name,
            "questions": qas,
            "total": MAX_QUESTIONS,
            "progress": f"0/{MAX_QUESTIONS}"
        })


class StaticAIAnswerBatchView(APIView):
    def post(self, request):
        test_name = request.data.get("test_name")
        section_name = request.data.get("section_name", "Middle School(13-15)")  # NEW!
        answers = request.data.get("answers", [])

        if test_name not in STATIC_TESTS:
            return Response({"error": f"Invalid test name: {test_name}"}, status=400)

        session_key = f"{request.session.session_key}-{test_name}-{section_name}"
        session = SESSION_STORE.get(session_key)

        if not session or not session.get("qas"):
            return Response({"error": "Session not found or questions not generated."}, status=404)

        qas = session["qas"]
        qid_map = {qa["question_id"]: qa for qa in qas}
        qas_with_answers = []

        for ans in answers:
            qid = ans.get("question_id")
            selected_option = ans.get("selected_option", "").lower()

            qa = qid_map.get(qid)
            if not qa or qa.get("answer"):
                continue

            selected_text = qa["options"].get(selected_option)
            if not selected_text:
                continue

            qa["answer"] = selected_text
            qa["selected_option"] = selected_option.upper()
            qa["answered_at"] = timezone.now().isoformat()
            qas_with_answers.append(qa)

        insights = evaluate_answers(test_name, qas_with_answers, section_name=section_name)
        for qa, insight in zip(qas_with_answers, insights):
            qa["evaluation"] = insight

        session["completed"] = all(q.get("answer") for q in qas)
        if session["completed"]:
            session["completed_at"] = timezone.now().isoformat()

        SESSION_STORE[session_key] = session

        return Response({
            "message": "Answers recorded.",
            "answered": len(qas_with_answers),
            "completed": session["completed"],
            "qas": session["qas"]
        })

class GenerateAssessmentReportView(APIView):
    def post(self, request):
        test_name = request.data.get("test_name")
        section_name = request.data.get("section_name", "Middle School(13-15)")

        if not test_name or test_name not in STATIC_TESTS:
            return Response({"error": "Invalid or missing test_name."}, status=400)

        session_key = f"{request.session.session_key}-{test_name}-{section_name}"
        session = SESSION_STORE.get(session_key)

        if not session:
            return Response({"error": "Session not found."}, status=404)

        if not session.get("completed"):
            return Response({"error": "Assessment not completed."}, status=400)

        qas = session.get("qas", [])
        test_data = STATIC_TESTS[test_name]
        test_description = test_data["description"]
        theory_content = test_data["theory"]

        report_paragraph = generate_detailed_assessment_report(
            test_name=test_name,
            theory_description=theory_content,
            test_description=test_description,
            qas=qas
        )

        return Response({
            "test_name": test_name,
            "section_name": section_name,
            "questions_answered": len([qa for qa in qas if qa.get("answer")]),
            "report": report_paragraph
        }, status=200)
