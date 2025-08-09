from rest_framework.exceptions import ValidationError

def validate_quiz_input(year_ids, type_ids, subject_id, topic_ids, quiz_group_name):
    if not year_ids or not type_ids or not subject_id or not topic_ids or not quiz_group_name:
        raise ValidationError("year_ids, type_ids, subject_id, topic_ids ve name parametrelerini eksiksiz ve doğru bir şekilde göndermelisiniz.")

    if not isinstance(subject_id, int):
        raise ValidationError("subject_id sayısal olmalıdır.")

    # Ensure year_ids, type_ids and topic_ids are lists of integers
    if not isinstance(topic_ids, list) or not all(isinstance(yid, int) for yid in topic_ids):
        raise ValidationError("topic_ids listesinde yalnızca sayısal değerler olmalıdır.")

    if not isinstance(year_ids, list) or not all(isinstance(yid, int) for yid in year_ids):
        raise ValidationError("year_ids listesinde yalnızca sayısal değerler olmalıdır.")

    if not isinstance(type_ids, list) or not all(isinstance(tid, int) for tid in type_ids):
        raise ValidationError("type_ids listesinde yalnızca sayısal değerler olmalıdır.")
