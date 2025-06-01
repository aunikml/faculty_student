# progress/templatetags/progress_tags.py
from django import template
from django.utils.html import format_html, mark_safe
from responseupload.models import Course
from managerpanel.models import Student # Assuming Student is in managerpanel
from progress.models import StudentManualCompletion # <-- Import the new model
import math

register = template.Library()

@register.simple_tag
def degree_progress_bar(student):
    if not isinstance(student, Student) or not student.batch or not student.batch.program:
        return mark_safe('<small class="text-muted">N/A (No Program/Batch)</small>')

    program = student.batch.program
    required_courses = Course.objects.filter(program=program).order_by('code')

    if not required_courses.exists():
         return mark_safe('<small class="text-muted">N/A (No courses for program)</small>')

    total_courses = required_courses.count()

    # --- Use StudentManualCompletion to determine completed courses ---
    manually_completed_course_ids = set(
        StudentManualCompletion.objects.filter(student=student)
        .values_list('course_id', flat=True)
    )
    # --- END ---

    progress_items_html = ""
    completed_count = 0
    segment_width_float = 100.0 / total_courses if total_courses > 0 else 0.0

    for i, course in enumerate(required_courses):
        # Check against manually_completed_course_ids
        is_completed = course.id in manually_completed_course_ids
        status_class = "bg-success" if is_completed else "bg-danger"
        tooltip_text = f"{course.code} - {course.name}"

        if is_completed:
            completed_count += 1
            # If you stored completion date/semester in StudentManualCompletion, you could fetch and display it
            tooltip_text += " (Manually Completed)"
        else:
             tooltip_text += " (Pending)"

        current_width_float = segment_width_float
        if i == total_courses - 1:
             current_width_float = 100.0 - (segment_width_float * (total_courses - 1))
        current_width_float = max(0, current_width_float)
        style_width_str = f"{current_width_float:.2f}"
        aria_valuenow_str = style_width_str

        progress_items_html += format_html(
            '<div class="progress-bar {status_class}" role="progressbar" style="width: {style_width}%;" '
            'aria-valuenow="{aria_valuenow}" aria-valuemin="0" aria-valuemax="100" '
            'data-bs-toggle="tooltip" data-bs-placement="top" title="{tooltip}">'
            '{code}'
            '</div>',
            status_class=status_class, style_width=style_width_str,
            aria_valuenow=aria_valuenow_str, tooltip=tooltip_text, code=course.code
        )

    progress_bar_html = format_html('<div class="progress" style="height: 18px;">{}</div>', mark_safe(progress_items_html))
    percentage_float = (completed_count / total_courses * 100.0) if total_courses > 0 else 0.0
    formatted_percentage_str = f"{percentage_float:.0f}"
    percentage_html = format_html(
        '<div class="text-muted text-end" style="font-size: 0.75rem; margin-top: 2px;">{completed}/{total} ({percentage_str}%)</div>',
        completed=completed_count, total=total_courses, percentage_str=formatted_percentage_str
    )
    return mark_safe(progress_bar_html + percentage_html)


@register.inclusion_tag('progress/partials/_editable_progress_inputs.html', takes_context=False)
def editable_progress_form_inputs(student):
    if not isinstance(student, Student) or not student.batch or not student.batch.program:
        return {'student': student, 'program_courses': [], 'completed_course_ids': []}

    program_courses = Course.objects.filter(program=student.batch.program).order_by('code')

    # --- Use StudentManualCompletion for initial checkbox state ---
    completed_course_ids = set(
        StudentManualCompletion.objects.filter(student=student, course__in=program_courses)
        .values_list('course_id', flat=True)
    )
    # --- END ---

    return {
        'student': student,
        'program_courses': program_courses,
        'completed_course_ids': completed_course_ids,
    }