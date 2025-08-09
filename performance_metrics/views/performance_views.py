from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from questions.models import Subject, Question
from quizzes.models import QuizAttempt, DisplaySetAttempt
from performance_metrics.models import SubjectPerformance
from serializers.performance_serializers import SubjectPerformanceSerializer
from utils.api_responses import ApiResponse
from pagination.custom_pagination import CustomPagination
from questions.models import Topic
from exam_sets.models import ExamSetQuizAttempt, ExamSetDisplaySetAttempt

class ExamTypePerformanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        subjects = Subject.objects.all()
            
        if not subjects.exists():
            return ApiResponse.NotFound(message='Ders bulunamadı.')
            
        performance_data = []
        total_correct = 0
        total_incorrect = 0
        total_unanswered = 0
        total_unseen = 0
        total_questions_overall = 0
        
        for subject in subjects:
            # Get all questions for this subject across all exam types
            all_questions = Question.objects.filter(subject=subject, image_url__isnull=False)
            total_questions = all_questions.count()
            total_questions_overall += total_questions
            
            # Get all question IDs
            all_question_ids = set(all_questions.values_list('id', flat=True))
            
            # Process quiz attempts
            quiz_attempts = QuizAttempt.objects.filter(
                user=user,
                quiz__quiz_group__subject=subject
            ).order_by('-created_at')

            # For standard display set attempts - use "subject" (singular)
            display_attempts = DisplaySetAttempt.objects.filter(
                user=user,
                display_set__subject=subject
            ).order_by('-created_at')

            # For exam set quiz attempts - use "subjects" (plural)
            exam_set_quiz_attempts = ExamSetQuizAttempt.objects.filter(
                user=user,
                quiz__quiz_group__subjects=subject
            ).order_by('-created_at')

            # For exam set display set attempts - use "subjects" (plural)
            exam_set_display_attempts = ExamSetDisplaySetAttempt.objects.filter(
                user=user,
                display_set__subjects=subject
            ).order_by('-created_at')
            
            # Track latest status for each question
            question_latest_status = {}  # {question_id: (status, timestamp)}
            
            # Process quiz attempts (newer to older)
            for attempt in quiz_attempts:
                attempt_time = attempt.created_at
                
                if 'answers' in attempt.details:
                    for answer in attempt.details['answers']:
                        question_id = answer.get('question_id')
                        if not question_id:
                            continue
                            
                        # Skip if we already have a more recent attempt for this question
                        if question_id in question_latest_status and question_latest_status[question_id][1] > attempt_time:
                            continue
                            
                        is_correct = answer.get('is_correct', False)
                        user_answer = answer.get('user_answer')
                        
                        if is_correct:
                            status = 'correct'
                        elif user_answer is None:
                            status = 'unanswered'
                        else:
                            status = 'incorrect'
                            
                        question_latest_status[question_id] = (status, attempt_time)
            
            # Process display set attempts (newer to older)
            for attempt in display_attempts:
                attempt_time = attempt.created_at
                
                if 'answers' in attempt.details:
                    for answer in attempt.details['answers']:
                        question_id = answer.get('id')
                        if not question_id:
                            continue
                            
                        # Skip if we already have a more recent attempt for this question
                        if question_id in question_latest_status and question_latest_status[question_id][1] > attempt_time:
                            continue
                            
                        is_correct = answer.get('is_correct', False)
                        user_answer = answer.get('user_answer')
                        
                        if is_correct:
                            status = 'correct'
                        elif user_answer is None:
                            status = 'unanswered'
                        else:
                            status = 'incorrect'
                            
                        question_latest_status[question_id] = (status, attempt_time)

            # Process exam set quiz attempts (newer to older)
            for attempt in exam_set_quiz_attempts:
                attempt_time = attempt.created_at
                
                if 'answers' in attempt.details:
                    for answer in attempt.details['answers']:
                        question_id = answer.get('question_id')
                        if not question_id:
                            continue

                        try:
                            question = Question.objects.get(id=question_id)
                            if question.subject_id != subject.id:
                                continue
                        except Question.DoesNotExist:
                            continue
                            
                        # Skip if we already have a more recent attempt for this question
                        if question_id in question_latest_status and question_latest_status[question_id][1] > attempt_time:
                            continue
                            
                        is_correct = answer.get('is_correct', False)
                        user_answer = answer.get('user_answer')
                        
                        if is_correct:
                            status = 'correct'
                        elif user_answer is None:
                            status = 'unanswered'
                        else:
                            status = 'incorrect'
                            
                        question_latest_status[question_id] = (status, attempt_time)
            
            # Process exam set display set attempts (newer to older)
            for attempt in exam_set_display_attempts:
                attempt_time = attempt.created_at
                
                if 'answers' in attempt.details:
                    for answer in attempt.details['answers']:
                        question_id = answer.get('id')
                        if not question_id:
                            continue

                        try:
                            question = Question.objects.get(id=question_id)
                            if question.subject_id != subject.id:
                                continue
                        except Question.DoesNotExist:
                            continue
                            
                        # Skip if we already have a more recent attempt for this question
                        if question_id in question_latest_status and question_latest_status[question_id][1] > attempt_time:
                            continue
                            
                        is_correct = answer.get('is_correct', False)
                        user_answer = answer.get('user_answer')
                        
                        if is_correct:
                            status = 'correct'
                        elif user_answer is None:
                            status = 'unanswered'
                        else:
                            status = 'incorrect'
                            
                        question_latest_status[question_id] = (status, attempt_time)
            
            # Calculate counts based on latest status
            correct_count = sum(1 for qid, (status, _) in question_latest_status.items() if status == 'correct')
            incorrect_count = sum(1 for qid, (status, _) in question_latest_status.items() if status == 'incorrect')
            unanswered_count = sum(1 for qid, (status, _) in question_latest_status.items() if status == 'unanswered')
            
            # Calculate unseen questions
            seen_questions = set(question_latest_status.keys())
            unseen_questions = all_question_ids - seen_questions
            unseen_count = len(unseen_questions)
            
            # Update totals
            total_correct += correct_count
            total_incorrect += incorrect_count
            total_unanswered += unanswered_count
            total_unseen += unseen_count
            
            # Calculate success rate and percentages
            attempted_count = correct_count + incorrect_count
            success_rate = (correct_count / attempted_count * 100) if attempted_count > 0 else 0
            
            # Calculate percentages
            correct_percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
            incorrect_percentage = (incorrect_count / total_questions * 100) if total_questions > 0 else 0
            unanswered_percentage = (unanswered_count / total_questions * 100) if total_questions > 0 else 0
            unseen_percentage = (unseen_count / total_questions * 100) if total_questions > 0 else 0
            
            # Get or create combined performance record
            subject_performance, _ = SubjectPerformance.objects.update_or_create(
                user=user,
                subject=subject,
                exam_type=None,  # No specific exam type
                defaults={
                    'correct_count': correct_count,
                    'incorrect_count': incorrect_count,
                    'unanswered_count': unanswered_count,
                    'unseen_count': unseen_count,
                    'total_questions': total_questions,
                    'success_rate': success_rate,
                    'correct_percentage': correct_percentage,
                    'incorrect_percentage': incorrect_percentage,
                    'unanswered_percentage': unanswered_percentage,
                    'unseen_percentage': unseen_percentage
                }
            )
            
            # Add to performance data
            performance_data.append({
                'id': subject_performance.id,
                'subject_id': subject.id,
                'subject_name': subject.name,
                'correct_count': correct_count,
                'incorrect_count': incorrect_count,
                'unanswered_count': unanswered_count,
                'unseen_count': unseen_count,
                'total_questions': total_questions,
                'success_rate': success_rate,
                'correct_percentage': round(correct_percentage, 1),
                'incorrect_percentage': round(incorrect_percentage, 1),
                'unanswered_percentage': round(unanswered_percentage, 1),
                'unseen_percentage': round(unseen_percentage, 1)
            })
        
        # Calculate overall success rate and percentages
        total_attempted = total_correct + total_incorrect
        overall_success_rate = (total_correct / total_attempted * 100) if total_attempted > 0 else 0
        
        overall_correct_percentage = (total_correct / total_questions_overall * 100) if total_questions_overall > 0 else 0
        overall_incorrect_percentage = (total_incorrect / total_questions_overall * 100) if total_questions_overall > 0 else 0
        overall_unanswered_percentage = (total_unanswered / total_questions_overall * 100) if total_questions_overall > 0 else 0
        overall_unseen_percentage = (total_unseen / total_questions_overall * 100) if total_questions_overall > 0 else 0
        
        return ApiResponse.Success(data={
            'subjects': performance_data,
            'overall': {
                'correct_count': total_correct,
                'incorrect_count': total_incorrect,
                'unanswered_count': total_unanswered,
                'unseen_count': total_unseen,
                'total_questions': total_questions_overall,
                'success_rate': overall_success_rate,
                'correct_percentage': round(overall_correct_percentage, 1),
                'incorrect_percentage': round(overall_incorrect_percentage, 1),
                'unanswered_percentage': round(overall_unanswered_percentage, 1),
                'unseen_percentage': round(overall_unseen_percentage, 1)
            }
        })

class SubjectPerformanceDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, exam_type_id, subject_id):
        user = request.user
        
        try:
            performance = SubjectPerformance.objects.get(
                user=user,
                exam_type_id=exam_type_id,
                subject_id=subject_id
            )
        except SubjectPerformance.DoesNotExist:
            return ApiResponse.NotFound(message='Bu ders için performans bilgisi bulunamadı.')
            
        serializer = SubjectPerformanceSerializer(performance, context={'request': request})
        return ApiResponse.Success(data=serializer.data)

class SubjectTopicsPerformanceView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, subject_id):
        user = request.user
        
        try:
            subject = Subject.objects.get(pk=subject_id)
        except Subject.DoesNotExist:
            return ApiResponse.NotFound(message='Ders bulunamadı.')
        
        # Get or calculate subject performance
        try:
            subject_performance = SubjectPerformance.objects.get(
                user=user,
                subject=subject,
                exam_type=None  # No specific exam type
            )
        except SubjectPerformance.DoesNotExist:
            # If performance doesn't exist, return 404
            return ApiResponse.NotFound(message='Bu ders için performans bilgisi bulunamadı.')
        
        # Get all topics for this subject
        topics = Topic.objects.filter(subject=subject).order_by('name')
        
        if not topics.exists():
            # Return just the subject performance if no topics exist
            return ApiResponse.Success(data={
                'subject': {
                    'id': subject.id,
                    'name': subject.name,
                    'correct_count': subject_performance.correct_count,
                    'incorrect_count': subject_performance.incorrect_count,
                    'unanswered_count': subject_performance.unanswered_count,
                    'unseen_count': subject_performance.unseen_count,
                    'total_questions': subject_performance.total_questions,
                    'success_rate': subject_performance.success_rate,
                    'correct_percentage': subject_performance.correct_percentage,
                    'incorrect_percentage': subject_performance.incorrect_percentage,
                    'unanswered_percentage': subject_performance.unanswered_percentage,
                    'unseen_percentage': subject_performance.unseen_percentage
                },
                'topics': []
            })
        
        topic_performances = []
        
        for topic in topics:
            # Get all questions for this topic and subject across all exam types
            all_questions = Question.objects.filter(
                subject=subject,
                topic=topic
            )
            total_questions = all_questions.count()
            
            if total_questions == 0:
                continue  # Skip topics with no questions
            
            # Get all question IDs
            all_question_ids = set(all_questions.values_list('id', flat=True))
            
            # Process quiz attempts
            quiz_attempts = QuizAttempt.objects.filter(
                user=user,
                quiz__quiz_group__subject=subject,
                quiz__quiz_group__topic=topic
            ).order_by('-created_at')

            display_attempts = DisplaySetAttempt.objects.filter(
                user=user,
                display_set__subject=subject,
                display_set__topic=topic
            ).order_by('-created_at')
            
            # Process exam set quiz attempts
            exam_set_quiz_attempts = ExamSetQuizAttempt.objects.filter(
                user=user,
                quiz__quiz_group__subjects=subject,
                quiz__quiz_group__topic=topic
            ).order_by('-created_at')
            
            # Process exam set display set attempts
            exam_set_display_attempts = ExamSetDisplaySetAttempt.objects.filter(
                user=user,
                display_set__subjects=subject,
                display_set__topic=topic
            ).order_by('-created_at')
            
            # Track latest status for each question
            question_latest_status = {}  # {question_id: (status, timestamp)}
            
            # Process quiz attempts (newer to older)
            for attempt in quiz_attempts:
                attempt_time = attempt.created_at
                
                if 'answers' in attempt.details:
                    for answer in attempt.details['answers']:
                        question_id = answer.get('question_id')
                        if not question_id:
                            continue
                        
                        # Check if this question belongs to our topic
                        try:
                            question = Question.objects.get(id=question_id)
                            if question.topic_id != topic.id:
                                continue
                        except Question.DoesNotExist:
                            continue
                        
                        # Skip if we already have a more recent attempt for this question
                        if question_id in question_latest_status and question_latest_status[question_id][1] > attempt_time:
                            continue
                            
                        is_correct = answer.get('is_correct', False)
                        user_answer = answer.get('user_answer')
                        
                        if is_correct:
                            status = 'correct'
                        elif user_answer is None:
                            status = 'unanswered'
                        else:
                            status = 'incorrect'
                            
                        question_latest_status[question_id] = (status, attempt_time)
            
            # Process display set attempts (newer to older)
            for attempt in display_attempts:
                attempt_time = attempt.created_at
                
                if 'answers' in attempt.details:
                    for answer in attempt.details['answers']:
                        question_id = answer.get('id')
                        if not question_id:
                            continue
                        
                        # Check if this question belongs to our topic
                        try:
                            question = Question.objects.get(id=question_id)
                            if question.topic_id != topic.id:
                                continue
                        except Question.DoesNotExist:
                            continue
                        
                        # Skip if we already have a more recent attempt for this question
                        if question_id in question_latest_status and question_latest_status[question_id][1] > attempt_time:
                            continue
                            
                        is_correct = answer.get('is_correct', False)
                        user_answer = answer.get('user_answer')
                        
                        if is_correct:
                            status = 'correct'
                        elif user_answer is None:
                            status = 'unanswered'
                        else:
                            status = 'incorrect'
                            
                        question_latest_status[question_id] = (status, attempt_time)
            
            # Process exam set quiz attempts (newer to older)
            for attempt in exam_set_quiz_attempts:
                attempt_time = attempt.created_at
                
                if 'answers' in attempt.details:
                    for answer in attempt.details['answers']:
                        question_id = answer.get('question_id')
                        if not question_id:
                            continue
                        
                        # Check if this question belongs to our topic
                        try:
                            question = Question.objects.get(id=question_id)
                            if question.topic_id != topic.id:
                                continue
                        except Question.DoesNotExist:
                            continue
                        
                        # Skip if we already have a more recent attempt for this question
                        if question_id in question_latest_status and question_latest_status[question_id][1] > attempt_time:
                            continue
                            
                        is_correct = answer.get('is_correct', False)
                        user_answer = answer.get('user_answer')
                        
                        if is_correct:
                            status = 'correct'
                        elif user_answer is None:
                            status = 'unanswered'
                        else:
                            status = 'incorrect'
                            
                        question_latest_status[question_id] = (status, attempt_time)
            
            # Process exam set display set attempts (newer to older)
            for attempt in exam_set_display_attempts:
                attempt_time = attempt.created_at
                
                if 'answers' in attempt.details:
                    for answer in attempt.details['answers']:
                        question_id = answer.get('id')
                        if not question_id:
                            continue
                        
                        # Check if this question belongs to our topic
                        try:
                            question = Question.objects.get(id=question_id)
                            if question.topic_id != topic.id:
                                continue
                        except Question.DoesNotExist:
                            continue
                        
                        # Skip if we already have a more recent attempt for this question
                        if question_id in question_latest_status and question_latest_status[question_id][1] > attempt_time:
                            continue
                            
                        is_correct = answer.get('is_correct', False)
                        user_answer = answer.get('user_answer')
                        
                        if is_correct:
                            status = 'correct'
                        elif user_answer is None:
                            status = 'unanswered'
                        else:
                            status = 'incorrect'
                            
                        question_latest_status[question_id] = (status, attempt_time)
            
            # Calculate counts based on latest status
            correct_count = sum(1 for qid, (status, _) in question_latest_status.items() if status == 'correct')
            incorrect_count = sum(1 for qid, (status, _) in question_latest_status.items() if status == 'incorrect')
            unanswered_count = sum(1 for qid, (status, _) in question_latest_status.items() if status == 'unanswered')
            
            # Calculate unseen questions
            seen_questions = set(question_latest_status.keys())
            unseen_questions = all_question_ids - seen_questions
            unseen_count = len(unseen_questions)
            
            # Calculate success rate
            attempted_count = correct_count + incorrect_count
            success_rate = (correct_count / attempted_count * 100) if attempted_count > 0 else 0
            
            # Add to topic performances
            topic_performances.append({
                'topic_id': topic.id,
                'topic_name': topic.name,
                'correct_count': correct_count,
                'incorrect_count': incorrect_count,
                'unanswered_count': unanswered_count,
                'unseen_count': unseen_count,
                'total_questions': total_questions,
                'success_rate': success_rate,
                'achievement_code': topic.achievement_code
            })
        
        # Apply pagination
        paginator = self.pagination_class()
        paginated_topics = paginator.paginate_queryset(topic_performances, request)
        
        # Return both subject performance and paginated topic performances
        response_data = {
            'subject': {
                'id': subject.id,
                'name': subject.name,
                'correct_count': subject_performance.correct_count,
                'incorrect_count': subject_performance.incorrect_count,
                'unanswered_count': subject_performance.unanswered_count,
                'unseen_count': subject_performance.unseen_count,
                'total_questions': subject_performance.total_questions,
                'success_rate': subject_performance.success_rate,
                'correct_percentage': subject_performance.correct_percentage,
                'incorrect_percentage': subject_performance.incorrect_percentage,
                'unanswered_percentage': subject_performance.unanswered_percentage,
                'unseen_percentage': subject_performance.unseen_percentage
            }
        }
        
        return paginator.get_paginated_response({'topics': paginated_topics, 'subject': response_data['subject']})
