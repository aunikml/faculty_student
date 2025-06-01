# managerpanel/views.py
import csv
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect, csrf_exempt # csrf_exempt only if truly needed and understood
from django.db import transaction, IntegrityError
from django.db.models import Q, Prefetch, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django import forms

from .models import (
    CourseAssignment, ManagerProfile, Batch, Student, Cohort,
    Course, Semester, Year, Program # Ensure all necessary models from this app are included
)
from .forms import (
    CourseAssignmentForm, BatchForm, StudentForm, StudentCSVUploadForm, StudentSearchForm
)
# Import from responseupload if forms are still there, or move them to managerpanel.forms
from responseupload.forms import (
    ProgramForm as RUProgramForm,
    CourseForm as RUCourseForm,
    SemesterForm as RUSemesterForm,
    YearForm as RUYearForm
)
# Import the template tag function directly to re-render the progress bar
from progress.templatetags.progress_tags import degree_progress_bar
# Import the new model for manual completions
from progress.models import StudentManualCompletion

# ==============================================================================
# Helper Functions
# ==============================================================================

def is_manager(user):
    if not user.is_authenticated: return False
    try: return user.managerprofile.is_manager
    except ManagerProfile.DoesNotExist: return False
    except AttributeError: return False

# ==============================================================================
# Manager Dashboard and Assignment Views
# ==============================================================================

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def manager_dashboard(request):
    student_search_form = StudentSearchForm(request.GET or None)
    context = {'student_search_form': student_search_form}
    return render(request, 'managerpanel/manager_dashboard.html', context)

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def create_course_assignment(request):
    if request.method == 'POST':
        form = CourseAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save()
            messages.success(request, f'Successfully assigned course {assignment.course.code}.')
            return redirect('managerpanel:list_assignments')
        else: messages.error(request, 'Please correct the errors below.')
    else: form = CourseAssignmentForm()
    context = {'form': form, 'form_title': 'Assign New Course'}
    return render(request, 'managerpanel/create_course_assignment.html', context)

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def edit_course_assignment(request, assignment_id):
    assignment = get_object_or_404(CourseAssignment.objects.select_related('course', 'semester', 'year', 'batch'), pk=assignment_id)
    if request.method == 'POST':
        form = CourseAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            messages.success(request, f'Successfully updated assignment for {assignment.course.code}.')
            return redirect('managerpanel:list_assignments')
        else: messages.error(request, 'Please correct the errors below.')
    else: form = CourseAssignmentForm(instance=assignment)
    context = {'form': form, 'assignment': assignment, 'form_title': f'Edit Assignment: {assignment.course.code}'}
    return render(request, 'managerpanel/edit_course_assignment.html', context)

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def delete_course_assignment(request, assignment_id):
    assignment = get_object_or_404(CourseAssignment.objects.select_related('course'), pk=assignment_id)
    if request.method == 'POST':
        course_code = assignment.course.code
        try: assignment.delete(); messages.success(request, f'Successfully deleted assignment for {course_code}.')
        except Exception as e: messages.error(request, f"Error deleting assignment: {e}")
        return redirect('managerpanel:list_assignments')
    context = {'assignment': assignment}
    return render(request, 'managerpanel/delete_course_assignment_confirm.html', context)

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def list_course_assignments(request):
    assignment_list = CourseAssignment.objects.select_related(
        'course', 'course__program', 'batch', 'batch__cohort', 'semester', 'year'
    ).prefetch_related('faculty_members').all()
    course_query = request.GET.get('course_q', '').strip()
    faculty_query = request.GET.get('faculty_q', '').strip()
    batch_query = request.GET.get('batch_q', '').strip()
    if course_query: assignment_list = assignment_list.filter(Q(course__code__icontains=course_query) | Q(course__name__icontains=course_query))
    if faculty_query: assignment_list = assignment_list.filter(Q(faculty_members__username__icontains=faculty_query) | Q(faculty_members__first_name__icontains=faculty_query) | Q(faculty_members__last_name__icontains=faculty_query)).distinct()
    if batch_query: assignment_list = assignment_list.filter(batch__name__icontains=batch_query)
    assignment_list = assignment_list.order_by('-year__name', '-semester__name', '-start_date', 'course__code')
    paginator = Paginator(assignment_list, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {'assignments_page': page_obj, 'course_query': course_query, 'faculty_query': faculty_query, 'batch_query': batch_query}
    return render(request, 'managerpanel/list_course_assignments.html', context)

# ==============================================================================
# Views for Creating Shared Academic Components
# ==============================================================================
@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
@csrf_protect
def handle_component_create_view(request, form_class, success_message, template_name, redirect_url_name):
    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            form.save(); messages.success(request, success_message); return redirect(redirect_url_name)
        else: messages.error(request, 'Please correct the errors below.')
    else: form = form_class()
    model_name = getattr(form_class._meta.model._meta, 'verbose_name', form_class._meta.model.__name__)
    form_title = f"Create New {model_name}"
    return render(request, template_name, {'form': form, 'form_title': form_title})

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def create_program_manager(request):
    return handle_component_create_view(request, RUProgramForm, 'Program created.', 'managerpanel/create_component.html', 'managerpanel:manager_dashboard')
@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def create_semester_manager(request):
    return handle_component_create_view(request, RUSemesterForm, 'Semester created.', 'managerpanel/create_component.html', 'managerpanel:manager_dashboard')
@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def create_year_manager(request):
    return handle_component_create_view(request, RUYearForm, 'Year created.', 'managerpanel/create_component.html', 'managerpanel:manager_dashboard')
@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def create_course_manager(request):
    return handle_component_create_view(request, RUCourseForm, 'Course definition created.', 'managerpanel/create_component.html', 'managerpanel:manager_dashboard')

# ==============================================================================
# Batch Management Views
# ==============================================================================
@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def list_batches(request):
    batches_list = Batch.objects.select_related('semester', 'cohort', 'program').annotate(student_count=Count('students')).order_by('-year', 'status', 'semester__name', 'name')
    paginator = Paginator(batches_list, 20)
    page_number = request.GET.get('page')
    batches_page = paginator.get_page(page_number)
    context = {'batches_page': batches_page}
    return render(request, 'managerpanel/list_batches.html', context)

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def create_batch(request):
    if request.method == 'POST':
        form = BatchForm(request.POST)
        if form.is_valid(): form.save(); messages.success(request, 'Batch created successfully.'); return redirect('managerpanel:list_batches')
        else: messages.error(request, 'Error creating batch. Please check the form.')
    else: form = BatchForm()
    return render(request, 'managerpanel/create_or_edit_batch.html', {'form': form, 'form_title': 'Create New Batch'})

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def edit_batch(request, batch_id):
    batch = get_object_or_404(Batch.objects.select_related('cohort', 'semester', 'program'), pk=batch_id)
    if request.method == 'POST':
        form = BatchForm(request.POST, instance=batch)
        if form.is_valid(): form.save(); messages.success(request, f'Batch "{batch.name}" updated successfully.'); return redirect('managerpanel:list_batches')
        else: messages.error(request, 'Error updating batch. Please check the form.')
    else: form = BatchForm(instance=batch)
    return render(request, 'managerpanel/create_or_edit_batch.html', {'form': form, 'batch': batch, 'form_title': f'Edit Batch: {batch.name}'})

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def delete_batch(request, batch_id):
    batch = get_object_or_404(Batch, pk=batch_id)
    student_count = batch.students.count()
    if request.method == 'POST':
        batch_name = batch.name
        try: batch.delete(); messages.success(request, f'Batch "{batch_name}" and its {student_count} student(s) deleted.');
        except Exception as e: messages.error(request, f'Error deleting batch "{batch_name}": {e}');
        return redirect('managerpanel:list_batches')
    context = {'batch': batch, 'student_count': student_count}
    return render(request, 'managerpanel/delete_batch_confirm.html', context)

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def batch_detail(request, batch_id):
    batch = get_object_or_404(Batch.objects.select_related('semester', 'cohort', 'program'), pk=batch_id)
    student_list = batch.students.select_related('enrollment_semester').all().order_by('last_name', 'first_name')
    paginator = Paginator(student_list, 20)
    page_number = request.GET.get('page')
    students_page = paginator.get_page(page_number)
    context = {'batch': batch, 'students_page': students_page}
    return render(request, 'managerpanel/batch_detail.html', context)

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
@require_POST
@csrf_protect
def update_batch_status(request, batch_id):
    batch = get_object_or_404(Batch, pk=batch_id)
    new_status = request.POST.get('status')
    valid_statuses = [choice[0] for choice in Batch.BATCH_STATUS_CHOICES]

    if new_status not in valid_statuses:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Invalid status provided.'}, status=400)
        messages.error(request, 'Invalid status provided.')
        return redirect('managerpanel:list_batches')

    try:
        batch.status = new_status
        batch.save()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Batch "{batch.name}" status updated to {batch.get_status_display()}.',
                'new_status_display': batch.get_status_display(),
                'new_status_value': batch.status
            })
        messages.success(request, f'Batch "{batch.name}" status updated to {batch.get_status_display()}.')
    except Exception as e:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
        messages.error(request, f'Error updating batch status: {e}')
    return redirect('managerpanel:list_batches')

# ==============================================================================
# Student Management Views
# ==============================================================================
@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def search_students(request):
    form = StudentSearchForm(request.GET or None)
    student_list = Student.objects.select_related('batch', 'batch__cohort', 'batch__program', 'enrollment_semester').all()
    query, status_filter, cohort_filter, degree_filter, program_filter_id = '', '', None, '', ''

    if form.is_valid():
        query = form.cleaned_data.get('query','').strip()
        status_filter = form.cleaned_data.get('status', '').strip()
        cohort_filter = form.cleaned_data.get('cohort')
        degree_filter = form.cleaned_data.get('degree', '').strip()
        program_filter_obj = form.cleaned_data.get('program')
        if program_filter_obj: program_filter_id = str(program_filter_obj.id)

        if query: student_list = student_list.filter(Q(student_id__icontains=query) | Q(email__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query))
        if status_filter: student_list = student_list.filter(status=status_filter)
        if cohort_filter: student_list = student_list.filter(batch__cohort=cohort_filter)
        if degree_filter: student_list = student_list.filter(degree=degree_filter)
        if program_filter_obj: student_list = student_list.filter(batch__program=program_filter_obj)

    student_list = student_list.order_by('batch__name', 'last_name', 'first_name')
    paginator = Paginator(student_list, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    results_found = student_list.exists() or not any([query, status_filter, cohort_filter, degree_filter, program_filter_id])

    context = {
        'form': form, 'students_page': page_obj, 'query': query,
        'status_filter': status_filter, 'cohort_filter': cohort_filter.id if cohort_filter else '',
        'degree_filter': degree_filter, 'program_filter': program_filter_id,
        'result_count': paginator.count, 'results_found': results_found
    }
    return render(request, 'managerpanel/search_students.html', context)

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def add_student_manual(request, batch_id):
    batch = get_object_or_404(Batch.objects.select_related('program'), pk=batch_id)
    if request.method == 'POST':
        form = StudentForm(request.POST, initial={'batch': batch})
        if form.is_valid():
            student = form.save(commit=False); student.batch = batch
            try: student.save(); messages.success(request, f'Student {student.first_name} {student.last_name} added to {batch.name}.'); return redirect('managerpanel:batch_detail', batch_id=batch.id)
            except IntegrityError as e: messages.error(request, f'Error: Student ID or Email likely already exists. ({e})')
            except Exception as e: messages.error(request, f'An unexpected error occurred: {e}')
        else: messages.error(request, 'Please correct the form errors.')
    else: form = StudentForm(initial={'batch': batch}); form.fields['batch'].widget = forms.HiddenInput()
    context = { 'form': form, 'batch': batch, 'form_title': f'Add Student to: {batch.name}'}
    return render(request, 'managerpanel/add_or_edit_student.html', context)

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def edit_student(request, student_id):
    student = get_object_or_404(Student.objects.select_related('batch'), pk=student_id)
    batch_id_for_redirect = student.batch.id if student.batch else None
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
             try: form.save(); messages.success(request, f'Student {student.first_name} {student.last_name} updated.')
             except IntegrityError as e: messages.error(request, f'Error: Unique constraint (ID/Email?) failed. ({e})')
             except Exception as e: messages.error(request, f'Error: {e}')
             else: return redirect('managerpanel:batch_detail', batch_id=batch_id_for_redirect) if batch_id_for_redirect else redirect('managerpanel:search_students')
        else: messages.error(request, 'Please correct the form errors.')
    else: form = StudentForm(instance=student)
    context = { 'form': form, 'student': student, 'batch': student.batch, 'form_title': f'Edit: {student.first_name} {student.last_name}'}
    return render(request, 'managerpanel/add_or_edit_student.html', context)

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def delete_student(request, student_id):
    student = get_object_or_404(Student.objects.select_related('batch'), pk=student_id)
    batch_id_for_redirect = student.batch.id if student.batch else None
    if request.method == 'POST':
        student_name = f"{student.first_name} {student.last_name}";
        try: student.delete(); messages.success(request, f'Student "{student_name}" deleted.');
        except Exception as e: messages.error(request, f'Error deleting student: {e}');
        return redirect('managerpanel:batch_detail', batch_id=batch_id_for_redirect) if batch_id_for_redirect else redirect('managerpanel:search_students')
    context = {'student': student, 'batch': student.batch }
    return render(request, 'managerpanel/delete_student_confirm.html', context)

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
@csrf_protect
def upload_students_csv(request):
    if request.method == 'POST':
        form = StudentCSVUploadForm(request.POST, request.FILES);
        if form.is_valid():
            batch = form.cleaned_data['batch']; csv_file = form.cleaned_data['csv_file'];
            if not csv_file.name.endswith('.csv'): messages.error(request, 'Invalid file type: Please upload a .csv file.'); return redirect('managerpanel:upload_students_csv')
            try:
                decoded_file = io.TextIOWrapper(csv_file.file, encoding='utf-8-sig'); reader = csv.DictReader(decoded_file);
                expected_headers_lower = {'student_id', 'first_name', 'last_name', 'email', 'enrollment_semester', 'status'};
                if not reader.fieldnames: messages.error(request, "CSV empty/no headers."); return redirect('managerpanel:upload_students_csv')
                actual_headers_lower = {h.strip().lower() for h in reader.fieldnames if h}; missing_required = expected_headers_lower - actual_headers_lower;
                if missing_required: messages.error(request, f"Missing headers: {', '.join(missing_required)}"); return redirect('managerpanel:upload_students_csv')
                created_count, updated_count, errors, processed_ids = 0, 0, [], set(); valid_semester_names = {s.name.lower(): s for s in Semester.objects.all()}; valid_statuses = [s[0] for s in Student.STATUS_CHOICES]; valid_degree_keys = {d[0] for d in Student.DEGREE_CHOICES};
                with transaction.atomic():
                    for row_num, row in enumerate(reader, start=2):
                        row_data = {k.strip().lower(): v.strip() for k, v in row.items() if k and v is not None};
                        student_id = row_data.get('student_id'); first_name = row_data.get('first_name'); last_name = row_data.get('last_name'); email = row_data.get('email'); phone = row_data.get('phone_number'); enrollment_sem_name = row_data.get('enrollment_semester'); status = row_data.get('status', 'active').lower(); degree_key = row_data.get('degree', '').lower(); notes = row_data.get('notes');
                        if not all([student_id, first_name, last_name, email, enrollment_sem_name, status]): errors.append(f"Row {row_num}: Missing required data."); continue
                        if student_id in processed_ids: errors.append(f"Row {row_num}: Duplicate ID '{student_id}' in CSV."); continue
                        if status not in valid_statuses: errors.append(f"Row {row_num}: Invalid status '{status}'."); continue
                        if degree_key and degree_key not in valid_degree_keys: errors.append(f"Row {row_num}: Invalid degree key '{degree_key}'. Valid: {', '.join(valid_degree_keys)}."); continue
                        enrollment_semester_obj = valid_semester_names.get(enrollment_sem_name.lower())
                        if not enrollment_semester_obj: errors.append(f"Row {row_num}: Semester '{enrollment_sem_name}' not found."); continue
                        student_data = {'batch': batch, 'first_name': first_name, 'last_name': last_name, 'email': email, 'phone_number': phone or None, 'enrollment_semester': enrollment_semester_obj, 'status': status, 'degree': degree_key or None, 'notes': notes or None}
                        try:
                            student, created = Student.objects.update_or_create(student_id=student_id, defaults=student_data)
                            processed_ids.add(student_id)
                            if created: created_count += 1
                            else: updated_count += 1
                        except IntegrityError as e: field = "Email" if "email" in str(e).lower() else "ID/field"; errors.append(f"Row {row_num}: Error for ID {student_id}. Unique constraint ({field}?).")
                        except Exception as e: errors.append(f"Row {row_num}: Error for ID {student_id}: {e}")
                if errors:
                    for error in errors: messages.warning(request, error);
                    messages.error(request, f"Upload completed: {len(errors)} error(s). Added: {created_count}, Updated: {updated_count}.")
                else: messages.success(request, f"Upload successful. Added: {created_count}, Updated: {updated_count}.")
                return redirect('managerpanel:batch_detail', batch_id=batch.id)
            except UnicodeDecodeError: messages.error(request, "Decoding error. Ensure CSV is UTF-8."); return redirect('managerpanel:upload_students_csv')
            except KeyError as e: messages.error(request, f"Header error: Missing {e}. Check headers."); return redirect('managerpanel:upload_students_csv')
            except Exception as e: messages.error(request, f"Processing error: {e}"); return redirect('managerpanel:upload_students_csv')
        else: messages.error(request, "Invalid form. Check fields.")
    else: form = StudentCSVUploadForm()
    return render(request, 'managerpanel/upload_students.html', {'form': form, 'form_title': 'Upload Students via CSV'})

# ==============================================================================
# Student Progress Editing Views
# ==============================================================================

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
@require_POST
@csrf_protect
def update_student_progress(request, student_id):
    student = get_object_or_404(Student.objects.select_related('batch__program'), pk=student_id)
    if not student.batch or not student.batch.program:
        return JsonResponse({'success': False, 'error': 'Student not associated with a batch or program.'}, status=400)

    submitted_completed_course_ids_str = request.POST.getlist('completed_courses')
    submitted_completed_course_ids = {int(cid) for cid in submitted_completed_course_ids_str if cid.isdigit()}

    try:
        with transaction.atomic():
            program_courses = Course.objects.filter(program=student.batch.program)
            # Delete existing manual completions for this student for courses within their program
            # that are NOT in the submitted list.
            StudentManualCompletion.objects.filter(
                student=student,
                course__in=program_courses # Only consider courses from the student's program
            ).exclude(course_id__in=submitted_completed_course_ids).delete()

            # Add new manual completions for submitted courses that are part of the program
            # and don't already have an entry.
            existing_completions_for_student = set(
                StudentManualCompletion.objects.filter(
                    student=student,
                    course_id__in=submitted_completed_course_ids
                ).values_list('course_id', flat=True)
            )
            
            completions_to_create = []
            for course_id in submitted_completed_course_ids:
                # Ensure course_id is valid and belongs to the student's program
                if course_id not in existing_completions_for_student and \
                   program_courses.filter(id=course_id).exists():
                    completions_to_create.append(
                        StudentManualCompletion(student=student, course_id=course_id)
                    )
            
            if completions_to_create:
                StudentManualCompletion.objects.bulk_create(completions_to_create)

        # After updating, re-render the progress bar
        # The degree_progress_bar tag now reads from StudentManualCompletion
        rendered_progress_html = degree_progress_bar(student)

        return JsonResponse({
            'success': True,
            'message': 'Student progress updated successfully.',
            'progress_html': rendered_progress_html
        })
    except Exception as e:
        # Log the error for debugging purposes on the server
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': f'An internal error occurred: {str(e)}'}, status=500)


@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def get_student_progress_edit_courses(request, student_id):
    student = get_object_or_404(Student.objects.select_related('batch__program'), pk=student_id)
    if not student.batch or not student.batch.program:
        return JsonResponse({'courses': [], 'completed_course_ids': [], 'error': 'Student not associated with a batch or program.'}, status=400)

    program_courses = Course.objects.filter(program=student.batch.program).order_by('code')
    
    # Get completed state from StudentManualCompletion model
    completed_course_ids = set(
        StudentManualCompletion.objects.filter(student=student, course__in=program_courses)
        .values_list('course_id', flat=True)
    )

    courses_data = [{'id': c.id, 'code': c.code, 'name': c.name} for c in program_courses]
    
    return JsonResponse({
        'courses': courses_data,
        'completed_course_ids': list(completed_course_ids)
    })