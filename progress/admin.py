# progress/admin.py
from django.contrib import admin
from .models import StudentManualCompletion

@admin.register(StudentManualCompletion)
class StudentManualCompletionAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'get_student_id', 'get_course_program')
    list_filter = ('student__batch__program', 'course__program', 'student__batch')
    search_fields = (
        'student__first_name', 'student__last_name', 'student__student_id',
        'course__code', 'course__name'
    )
    list_select_related = ('student', 'course', 'student__batch', 'course__program')
    autocomplete_fields = ['student', 'course'] # For easier selection

    @admin.display(description="Student ID", ordering="student__student_id")
    def get_student_id(self, obj):
        return obj.student.student_id

    @admin.display(description="Course Program", ordering="course__program__code")
    def get_course_program(self, obj):
        return obj.course.program.code if obj.course and obj.course.program else "-"