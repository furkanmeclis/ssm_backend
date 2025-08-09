from rest_framework.exceptions import ValidationError

def validate_quiz_input(year_ids, type_ids, subject_id, topic_id, quiz_group_name):
    if not year_ids or not type_ids or not subject_id or not topic_id or not quiz_group_name:
        raise ValidationError("year_ids, type_ids, subject_id, topic_id ve name parametrelerini eksiksiz ve doğru bir şekilde göndermelisiniz.")

    if not isinstance(subject_id, int) or not isinstance(topic_id, int):
        raise ValidationError("subject_id ve topic_id sayısal olmalıdır.")

    # Ensure year_ids and type_ids are lists of integers
    if not isinstance(year_ids, list) or not all(isinstance(yid, int) for yid in year_ids):
        raise ValidationError("year_ids listesinde yalnızca sayısal değerler olmalıdır.")

    if not isinstance(type_ids, list) or not all(isinstance(tid, int) for tid in type_ids):
        raise ValidationError("type_ids listesinde yalnızca sayısal değerler olmalıdır.")
