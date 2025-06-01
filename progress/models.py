# progress/models.py
from django.db import models
from managerpanel.models import Student # Assuming Student is in managerpanel
from responseupload.models import Course # Assuming Course is in responseupload

class StudentManualCompletion(models.Model):
    """
    Stores manually set completion status for a student for a specific course.
    This overrides or complements progress inferred from CourseAssignments.
    """
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='manual_completions'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='manual_student_completions'
    )
    # completed_on = models.DateField(null=True, blank=True, help_text="Date when the course was manually marked as completed.")
    # notes = models.TextField(blank=True, null=True, help_text="Optional notes about this manual completion.")

    class Meta:
        unique_together = ('student', 'course') # A student can only have one manual completion entry per course
        verbose_name = "Student Manual Course Completion"
        verbose_name_plural = "Student Manual Course Completions"
        ordering = ['student', 'course__code']

    def __str__(self):
        return f"{self.student} - {self.course.code} (Manually Marked)"