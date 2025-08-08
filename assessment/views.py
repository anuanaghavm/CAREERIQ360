# views.py - Fixed version with proper error handling
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.conf import settings
from .utils.ai_assessment import generate_questions, evaluate_answers, STATIC_TESTS, generate_ai_report,get_report_from_cache,save_report_to_cache
from login.models import CustomUser
import json
import threading
import time
import logging
import traceback
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from django.core.cache import cache
import tempfile
import os
import openai
import httpx  # Added httpx import

# Setup logging
logger = logging.getLogger(__name__)

SESSION_STORE = {}
REPORTS_STORE = {}
MAX_QUESTIONS = 30

# Thread pool for background processing with error handling
executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="assessment_worker")

class StaticAIQuestionBatchView(APIView):
    def post(self, request):
        """Generate questions with comprehensive error handling"""
        try:
            # Extract and validate request data
            test_name = request.data.get("test_name")
            section_name = request.data.get("section_name", "Middle School(13-15)")
            uuid = request.data.get("uuid")

            # Validation
            if not test_name:
                return Response({"error": "test_name is required"}, status=400)
            
            if test_name not in STATIC_TESTS:
                return Response({
                    "error": f"Invalid test name: {test_name}",
                    "available_tests": list(STATIC_TESTS.keys())
                }, status=400)

            if not uuid:
                return Response({"error": "UUID is required"}, status=400)
            
            # Validate user exists
            try:
                user = CustomUser.objects.get(uuid=uuid)
                user_data = {
                    'country': getattr(user, 'country', 'Unknown'),
                    'city': getattr(user, 'city', 'Unknown'),
                    'age': getattr(user, 'age', 15),
                    'section': section_name,
                    'study': getattr(user, 'study_background', 'General'),
                    'is_student': getattr(user, 'is_student', True)
                }
            except CustomUser.DoesNotExist:
                return Response({"error": "Invalid UUID"}, status=404)
            except Exception as e:
                logger.error(f"Database error while fetching user: {e}")
                return Response({"error": "Database error occurred"}, status=500)

            session_key = f"{uuid}-{test_name}-{section_name}"
            
            # Check existing session
            existing_session = SESSION_STORE.get(session_key)
            if existing_session and existing_session.get("qas") and len(existing_session["qas"]) >= MAX_QUESTIONS:
                logger.info(f"Returning existing session for {test_name}")
                return Response({
                    "test_name": test_name,
                    "section": section_name,
                    "uuid": uuid,
                    "questions": existing_session["qas"],
                    "total": MAX_QUESTIONS,
                    "progress": f"0/{MAX_QUESTIONS}",
                    "status": "ready",
                    "cached": True
                })

            # Generate questions with proper error handling
            logger.info(f"Starting question generation for {test_name}")
            start_time = time.time()
            
            try:
                # Call generate_questions with user_data
                qas = generate_questions(test_name, user_data, section_name, MAX_QUESTIONS)
                
            except httpx.TimeoutException as e:  # Fixed: Use httpx.TimeoutException
                logger.error(f"Request timeout for {test_name}: {e}")
                return Response({
                    "error": "Service timeout. Please try again in a moment.",
                    "error_code": "REQUEST_TIMEOUT",
                    "retry_suggestion": "Wait 30-60 seconds and try again"
                }, status=504)
                
            except openai.RateLimitError as e:
                logger.error(f"OpenAI rate limit for {test_name}: {e}")
                return Response({
                    "error": "Rate limit exceeded. Please wait before trying again.",
                    "error_code": "RATE_LIMIT",
                    "retry_suggestion": "Wait 2-3 minutes and try again"
                }, status=429)
                
            except openai.AuthenticationError as e:
                logger.error(f"OpenAI authentication error: {e}")
                return Response({
                    "error": "Service authentication error. Please contact administrator.",
                    "error_code": "AUTH_ERROR"
                }, status=503)
                
            except openai.APIError as e:
                logger.error(f"OpenAI API error for {test_name}: {e}")
                return Response({
                    "error": "OpenAI service error. Please try again.",
                    "error_code": "API_ERROR",
                    "retry_suggestion": "Try again in a few minutes"
                }, status=503)
                
            except (OSError, IOError, ConnectionError) as e:
                logger.error(f"Network/IO error during question generation: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                
                # Check if it's a specific network issue
                error_msg = str(e).lower()
                if "connection" in error_msg or "network" in error_msg:
                    return Response({
                        "error": "Network connectivity issue. Please check your internet connection.",
                        "error_code": "NETWORK_ERROR",
                        "retry_suggestion": "Check internet connection and try again"
                    }, status=503)
                elif "timeout" in error_msg:
                    return Response({
                        "error": "Network timeout occurred. Please try again.",
                        "error_code": "NETWORK_TIMEOUT", 
                        "retry_suggestion": "Try again in a few moments"
                    }, status=504)
                else:
                    return Response({
                        "error": "System I/O error occurred. Please try again.",
                        "error_code": "IO_ERROR",
                        "retry_suggestion": "Please wait a moment and try again",
                        "debug_info": str(e) if settings.DEBUG else None
                    }, status=500)
                    
            except FutureTimeoutError as e:
                logger.error(f"Generation timeout for {test_name}: {e}")
                return Response({
                    "error": "Question generation timed out. Please try again.",
                    "error_code": "GENERATION_TIMEOUT",
                    "retry_suggestion": "Try again in a few moments"
                }, status=504)
                
            except Exception as e:
                logger.error(f"Unexpected error generating questions for {test_name}: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return Response({
                    "error": "An unexpected error occurred during question generation.",
                    "error_code": "GENERATION_ERROR",
                    "debug_info": str(e) if settings.DEBUG else None,
                    "retry_suggestion": "Please try again"
                }, status=500)

            # Validate generated questions
            if not qas or len(qas) == 0:
                logger.error(f"No questions generated for {test_name}")
                return Response({
                    "error": "Failed to generate questions. Please try again.",
                    "error_code": "NO_QUESTIONS_GENERATED",
                    "debug_info": f"Empty response from question generator for {test_name}"
                }, status=500)

            # Validate question structure
            valid_qas = []
            for i, qa in enumerate(qas):
                if not isinstance(qa, dict):
                    logger.warning(f"Invalid question format at index {i}")
                    continue
                
                if not qa.get("question") or not qa.get("options"):
                    logger.warning(f"Missing question or options at index {i}")
                    continue
                
                # Prepare question with metadata
                qa["question_id"] = len(valid_qas) + 1
                qa["answer"] = None
                qa["selected_option"] = None
                qa["evaluation"] = None
                qa["generated_at"] = timezone.now().isoformat()
                valid_qas.append(qa)

            if len(valid_qas) < 10:  # Minimum threshold
                logger.error(f"Insufficient valid questions generated: {len(valid_qas)}")
                return Response({
                    "error": "Insufficient questions generated. Please try again.",
                    "error_code": "INSUFFICIENT_QUESTIONS",
                    "debug_info": f"Only {len(valid_qas)} valid questions out of {len(qas)} total"
                }, status=500)

            # Create session
            try:
                session = {
                    "uuid": uuid,
                    "user_email": getattr(user, 'email', 'unknown'),
                    "qas": valid_qas[:MAX_QUESTIONS],  # Ensure max limit
                    "completed": False,
                    "started_at": timezone.now().isoformat(),
                    "section": section_name,
                    "test_name": test_name,
                    "generation_info": {
                        "total_generated": len(qas),
                        "valid_questions": len(valid_qas),
                        "generation_time": time.time() - start_time
                    }
                }
                SESSION_STORE[session_key] = session
                
            except Exception as e:
                logger.error(f"Error creating session: {e}")
                return Response({
                    "error": "Failed to create session",
                    "error_code": "SESSION_CREATION_ERROR",
                    "debug_info": str(e)
                }, status=500)

            elapsed_time = time.time() - start_time
            logger.info(f"Generated {len(valid_qas)} questions for {test_name} in {elapsed_time:.2f} seconds")

            return Response({
                "test_name": test_name,
                "section": section_name,
                "uuid": uuid,
                "questions": valid_qas[:MAX_QUESTIONS],
                "total": len(valid_qas[:MAX_QUESTIONS]),
                "progress": f"0/{len(valid_qas[:MAX_QUESTIONS])}",
                "generation_time": f"{elapsed_time:.2f}s",
                "status": "success"
            })

        except Exception as e:
            # Catch-all for any other errors
            logger.error(f"Critical error in StaticAIQuestionBatchView: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response({
                "error": "A critical error occurred. Please try again.",
                "error_code": "CRITICAL_ERROR",
                "debug_info": str(e) if settings.DEBUG else None
            }, status=500)

class StaticAIAnswerBatchView(APIView):
    def post(self, request):
        """Process answers with comprehensive error handling"""
        try:
            # Extract and validate data
            test_name = request.data.get("test_name")
            section_name = request.data.get("section_name", "Middle School(13-15)")
            uuid = request.data.get("uuid")
            answers = request.data.get("answers", [])

            # Validation
            if not test_name or test_name not in STATIC_TESTS:
                return Response({"error": "Invalid test name"}, status=400)

            if not uuid:
                return Response({"error": "UUID is required"}, status=400)

            if not isinstance(answers, list):
                return Response({"error": "Answers must be a list"}, status=400)

            session_key = f"{uuid}-{test_name}-{section_name}"
            session = SESSION_STORE.get(session_key)

            if not session or not session.get("qas"):
                return Response({
                    "error": "Session not found or questions not generated",
                    "error_code": "SESSION_NOT_FOUND",
                    "suggestion": "Please generate questions first"
                }, status=404)

            # Process answers safely
            qas = session["qas"]
            qid_map = {qa["question_id"]: qa for qa in qas}
            qas_with_answers = []
            processing_errors = []

            for ans in answers:
                try:
                    qid = ans.get("question_id")
                    selected_option = ans.get("selected_option", "").lower()

                    if not qid or qid not in qid_map:
                        processing_errors.append(f"Invalid question ID: {qid}")
                        continue

                    qa = qid_map[qid]
                    if qa.get("answer"):  # Already answered
                        continue

                    selected_text = qa["options"].get(selected_option)
                    if not selected_text:
                        processing_errors.append(f"Invalid option for question {qid}: {selected_option}")
                        continue

                    qa["answer"] = selected_text
                    qa["selected_option"] = selected_option.upper()
                    qa["answered_at"] = timezone.now().isoformat()
                    qas_with_answers.append(qa)

                except Exception as e:
                    processing_errors.append(f"Error processing answer for question {ans.get('question_id')}: {str(e)}")
                    logger.warning(f"Answer processing error: {e}")

            # Start background evaluation if we have answers
            if qas_with_answers:
                try:
                    future = executor.submit(
                        self._evaluate_answers_background, 
                        session_key, test_name, qas_with_answers, section_name
                    )
                except Exception as e:
                    logger.error(f"Failed to start background evaluation: {e}")
                    # Continue without background evaluation

            # Update session
            try:
                session["completed"] = all(q.get("answer") for q in qas)
                if session["completed"]:
                    session["completed_at"] = timezone.now().isoformat()
                
                SESSION_STORE[session_key] = session
            except Exception as e:
                logger.error(f"Error updating session: {e}")
                return Response({
                    "error": "Failed to update session",
                    "error_code": "SESSION_UPDATE_ERROR",
                    "debug_info": str(e)
                }, status=500)

            response_data = {
                "message": "Answers recorded successfully",
                "uuid": uuid,
                "answered": len(qas_with_answers),
                "completed": session["completed"],
                "qas": session["qas"]
            }

            if processing_errors:
                response_data["warnings"] = processing_errors

            return Response(response_data)

        except Exception as e:
            logger.error(f"Critical error in StaticAIAnswerBatchView: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response({
                "error": "A critical error occurred while processing answers",
                "error_code": "ANSWER_PROCESSING_ERROR",
                "debug_info": str(e) if settings.DEBUG else None
            }, status=500)

    def _evaluate_answers_background(self, session_key, test_name, qas_with_answers, section_name):
        """Background evaluation with comprehensive error handling"""
        try:
            logger.info(f"Starting background evaluation for {len(qas_with_answers)} answers")
            start_time = time.time()
            
            # Call evaluate_answers with proper error handling
            try:
                insights = evaluate_answers(test_name, qas_with_answers, section_name)
            except httpx.TimeoutException as e:  # Fixed: Use httpx.TimeoutException
                logger.error(f"Request timeout during evaluation: {e}")
                insights = [f"Evaluation temporarily unavailable due to timeout" for _ in qas_with_answers]
            except openai.RateLimitError as e:
                logger.error(f"OpenAI rate limit during evaluation: {e}")
                insights = [f"Evaluation temporarily unavailable due to rate limit" for _ in qas_with_answers]
            except (OSError, IOError, ConnectionError) as e:
                logger.error(f"Network error during evaluation: {e}")
                insights = [f"Evaluation temporarily unavailable due to network error" for _ in qas_with_answers]
            except Exception as e:
                logger.error(f"Unexpected error during evaluation: {e}")
                insights = [f"Evaluation temporarily unavailable" for _ in qas_with_answers]
            
            # Update session with evaluations
            if session_key in SESSION_STORE:
                session = SESSION_STORE[session_key]
                qas = session.get("qas", [])
                
                for qa, insight in zip(qas_with_answers, insights):
                    qa["evaluation"] = insight
                
                session["evaluation_completed"] = True
                session["evaluation_completed_at"] = timezone.now().isoformat()
                SESSION_STORE[session_key] = session
                
                elapsed = time.time() - start_time
                logger.info(f"Background evaluation completed in {elapsed:.2f}s")
                
        except Exception as e:
            logger.error(f"Background evaluation failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Update session to indicate evaluation failed
            if session_key in SESSION_STORE:
                try:
                    session = SESSION_STORE[session_key]
                    session["evaluation_failed"] = True
                    session["evaluation_error"] = str(e)
                    SESSION_STORE[session_key] = session
                except Exception as session_error:
                    logger.error(f"Failed to update session with evaluation error: {session_error}")

class GenerateAssessmentReportView(APIView):
    """Generate comprehensive AI assessment report"""
    
    def post(self, request):
        try:
            test_name = request.data.get("test_name")
            section_name = request.data.get("section_name", "Middle School(13-15)")
            user_uuid = request.data.get("uuid")

            # Validation
            if not test_name or test_name not in STATIC_TESTS:
                return Response({"error": "Invalid test name"}, status=400)

            if not user_uuid:
                return Response({"error": "UUID is required"}, status=400)

            # Get user data
            try:
                user = CustomUser.objects.get(uuid=user_uuid)
                user_data = {
                    'country': getattr(user, 'country', 'Unknown'),
                    'city': getattr(user, 'city', 'Unknown'),
                    'age': getattr(user, 'age', 15),
                    'section': section_name,
                    'email': getattr(user, 'email', 'unknown')
                }
            except CustomUser.DoesNotExist:
                return Response({"error": "Invalid UUID"}, status=404)

            # Get session data
            session_key = f"{user_uuid}-{test_name}-{section_name}"
            session = SESSION_STORE.get(session_key)

            if not session or not session.get("completed"):
                return Response({
                    "error": "Assessment not completed",
                    "error_code": "INCOMPLETE_ASSESSMENT",
                    "suggestion": "Complete the assessment first"
                }, status=400)

            # Extract answers
            answers = []
            for qa in session.get("qas", []):
                if qa.get("answer"):
                    answers.append({
                        "question_id": qa.get("question_id"),
                        "question": qa.get("question"),
                        "selected_option": qa.get("selected_option"),
                        "answer": qa.get("answer"),
                        "evaluation": qa.get("evaluation")
                    })

            if not answers:
                return Response({
                    "error": "No answers found",
                    "error_code": "NO_ANSWERS"
                }, status=400)

            # Generate AI report
            try:
                report_data = generate_ai_report(test_name, answers, user_data)
                
                # Save to cache
                report_id = save_report_to_cache(report_data)
                
                # Store in memory (optional)
                REPORTS_STORE[report_id] = {
                    **report_data,
                    "generated_at": timezone.now().isoformat(),
                    "user_uuid": user_uuid
                }

                return Response({
                    "message": "Report generated successfully",
                    "report_id": report_id,
                    "report": report_data,
                    "status": "success"
                })

            except Exception as e:
                logger.error(f"Report generation error: {e}")
                return Response({
                    "error": "Failed to generate report",
                    "error_code": "REPORT_GENERATION_ERROR",
                    "debug_info": str(e) if settings.DEBUG else None
                }, status=500)

        except Exception as e:
            logger.error(f"Critical error in report generation: {e}")
            return Response({
                "error": "Critical error occurred",
                "error_code": "CRITICAL_ERROR",
                "debug_info": str(e) if settings.DEBUG else None
            }, status=500)


class GetSpecificReportView(APIView):
    """Get a specific report by ID"""
    
    def get(self, request, report_id):
        try:
            # Try cache first
            report_data = get_report_from_cache(report_id)
            
            # Fallback to memory store
            if not report_data:
                report_data = REPORTS_STORE.get(report_id)
            
            if not report_data:
                return Response({
                    "error": "Report not found",
                    "error_code": "REPORT_NOT_FOUND"
                }, status=404)

            return Response({
                "report_id": report_id,
                "report": report_data,
                "status": "success"
            })

        except Exception as e:
            logger.error(f"Error retrieving report {report_id}: {e}")
            return Response({
                "error": "Failed to retrieve report",
                "error_code": "RETRIEVAL_ERROR",
                "debug_info": str(e) if settings.DEBUG else None
            }, status=500)


class GetUserReportsView(APIView):
    """Get all reports for a specific user"""
    
    def get(self, request, uuid):
        try:
            # Filter reports by user UUID from memory store
            user_reports = []
            for report_id, report_data in REPORTS_STORE.items():
                if report_data.get("user_uuid") == uuid:
                    user_reports.append({
                        "report_id": report_id,
                        "test_name": report_data.get("test_name"),
                        "section_name": report_data.get("section_name"),
                        "generated_at": report_data.get("generated_at"),
                        "assessment_date": report_data.get("assessment_date")
                    })

            # Sort by generated_at desc
            user_reports.sort(key=lambda x: x.get("generated_at", ""), reverse=True)

            return Response({
                "uuid": uuid,
                "reports": user_reports,
                "total": len(user_reports),
                "status": "success"
            })

        except Exception as e:
            logger.error(f"Error retrieving user reports for {uuid}: {e}")
            return Response({
                "error": "Failed to retrieve user reports",
                "error_code": "USER_REPORTS_ERROR",
                "debug_info": str(e) if settings.DEBUG else None
            }, status=500)


class GetUserSessionsView(APIView):
    """Get all sessions for a specific user"""
    
    def get(self, request, uuid):
        try:
            # Filter sessions by user UUID
            user_sessions = []
            for session_key, session_data in SESSION_STORE.items():
                if session_data.get("uuid") == uuid:
                    user_sessions.append({
                        "session_key": session_key,
                        "test_name": session_data.get("test_name"),
                        "section": session_data.get("section"),
                        "completed": session_data.get("completed", False),
                        "started_at": session_data.get("started_at"),
                        "completed_at": session_data.get("completed_at"),
                        "total_questions": len(session_data.get("qas", [])),
                        "answered_questions": len([qa for qa in session_data.get("qas", []) if qa.get("answer")]),
                        "evaluation_completed": session_data.get("evaluation_completed", False)
                    })

            # Sort by started_at desc
            user_sessions.sort(key=lambda x: x.get("started_at", ""), reverse=True)

            return Response({
                "uuid": uuid,
                "sessions": user_sessions,
                "total": len(user_sessions),
                "status": "success"
            })

        except Exception as e:
            logger.error(f"Error retrieving user sessions for {uuid}: {e}")
            return Response({
                "error": "Failed to retrieve user sessions",
                "error_code": "USER_SESSIONS_ERROR",
                "debug_info": str(e) if settings.DEBUG else None
            }, status=500)
