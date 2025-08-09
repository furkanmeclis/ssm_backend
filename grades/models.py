from django.db import models

class GradeLevel(models.IntegerChoices):
    GRADE_6 = 6, '6. Sınıf'
    GRADE_7 = 7, '7. Sınıf'
    GRADE_8 = 8, '8. Sınıf'
    GRADE_9 = 9, '9. Sınıf'
    GRADE_10 = 10, '10. Sınıf'
    GRADE_11 = 11, '11. Sınıf'
    GRADE_12 = 12, '12. Sınıf'
    UNIVERSITY = 13, 'Üniversite'
