# responseupload/admin.py
from django.contrib import admin
from .models import (
    Program,
    Course,
    Faculty,
    FacultyResponse,
    CourseResponse,
    Semester,
    Year
)
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django import forms
import csv
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

# Use default UserAdmin for the User model
# admin.site.register(User, UserAdmin)

class FacultyResponseAdminForm(forms.ModelForm):
    faculty = forms.ModelChoiceField(queryset=User.objects.all(), required=True)
    course = forms.ModelChoiceField(queryset=Course.objects.all(), required=True)
    semester = forms.ModelChoiceField(queryset=Semester.objects.all(), required=True)
    year = forms.ModelChoiceField(queryset=Year.objects.all(), required=True)
    file = forms.FileField(label='Upload Faculty CSV', required=False)

    class Meta:
        model = FacultyResponse
        fields = '__all__'
        exclude = ('timestamp',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            try:
                self.fields['semester'].initial = self.instance.semester
                self.fields['course'].initial = self.instance.course
                self.fields['faculty'].initial = self.instance.faculty
                self.fields['year'].initial = self.instance.year
            except (FacultyResponse.DoesNotExist, AttributeError):
                pass

class CourseResponseAdminForm(forms.ModelForm):
    faculty = forms.ModelChoiceField(queryset=User.objects.all(), required=True)
    course = forms.ModelChoiceField(queryset=Course.objects.all(), required=True)
    semester = forms.ModelChoiceField(queryset=Semester.objects.all(), required=True)
    year = forms.ModelChoiceField(queryset=Year.objects.all(), required=True)
    file = forms.FileField(label='Upload Course CSV', required=False)

    class Meta:
        model = CourseResponse
        fields = '__all__'
        exclude = ('timestamp',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            try:
                self.fields['semester'].initial = self.instance.semester
                self.fields['course'].initial = self.instance.course
                self.fields['faculty'].initial = self.instance.faculty
                self.fields['year'].initial = self.instance.year
            except (CourseResponse.DoesNotExist, AttributeError):
                pass

class FacultyResponseAdmin(admin.ModelAdmin):
    def response_add(self, request, obj, post_url_continue=None):
        if '_addanother' not in request.POST and '_continue' not in request.POST and '_save' in request.POST:
            # Redirect to dashboard after successful upload
            messages.success(request, 'Faculty response uploaded successfully.')
            return HttpResponseRedirect(reverse('admin:index'))
        else:
            return super().response_add(request, obj, post_url_continue)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:  # Only send email for new objects
            course = obj.course
            subject = 'Your Faculty Evaluation Report Has Been Uploaded'
            # Safely handle potentially missing fields
            section = getattr(course, 'section', 'N/A')
            semester = getattr(course, 'semester', 'N/A')
            year = getattr(course, 'year', 'N/A')
            message = (
                f'Your evaluation report for Course {course.code} - {course.name} '
                f'(Section: {section}, Semester: {semester}, Year: {year}) '
                f'has been uploaded. Please login to the reporting system.\n'
                f'{request.build_absolute_uri(reverse("responseupload:login"))}'
            )
            recipient_list = [obj.faculty.email]  # Send to the assigned faculty
            from_email = settings.DEFAULT_FROM_EMAIL

            send_mail(subject, message, from_email, recipient_list)

    list_display = ('course', 'semester', 'year', 'faculty')
    list_filter = ('course', 'semester')
    search_fields = ('course__name', 'general_comments')  # Search by course name
    form = FacultyResponseAdminForm

    def add_view(self, request, form_url='', extra_context=None):
        if request.method == 'POST':
            form = FacultyResponseAdminForm(request.POST, request.FILES)
            if form.is_valid():
                semester = form.cleaned_data['semester']
                course = form.cleaned_data['course']
                faculty_member = form.cleaned_data['faculty']
                year = form.cleaned_data['year']
                
                csv_file = form.cleaned_data['file']
                if csv_file:
                    if not csv_file.name.endswith('.csv'):
                        messages.error(request, 'Please upload a CSV file.', request)
                        return super().add_view(request, form_url, extra_context)
            
                    decoded_file = csv_file.read().decode('utf-8').splitlines()
                    reader = csv.DictReader(decoded_file)
                    records_added = 0
                    for row in reader:
                        try:
                            timestamp = row.get('Timestamp')  # Adjust to your actual column name if needed
                            if timestamp:
                                faculty_response = FacultyResponse(
                                    semester=semester,
                                    course=course,
                                    year=year,
                                    faculty=faculty_member,
                                    q1=row.get('1. The organization of session materials and contents prepared by the instructor was-  '),
                                    q2=row.get("2. Instructor's effort to make the concept clear to the class was-"),
                                    q3=row.get('3. The teaching learning methods (e.g., lecture, group work) followed by the instructor was-'),
                                    q4=row.get("4. The use of learning materials/ resources/ examples/ cases, etc. by the instructor was-"),
                                    q5=row.get("5. Instructor's effort to engage the students in learning was-"),
                                    q6=row.get("6. Instructor’s encouragement for the participation, discussion and questions from students was-"),
                                    q7=row.get("7. The guidance for assignment/class activity (group work, presentation, etc.) provided by the instructor was-"),
                                    q8=row.get('8. Instructor’s class time management was-'),
                                    general_comments=row.get('General comments', ''),
                                )
                                faculty_response.save()
                                records_added += 1
                            else:
                                messages.error(request, "Timestamp is missing in the csv", request)
                                return super().add_view(request, form_url, extra_context)
                        except Exception as e:
                            messages.error(request, f"Error processing row: {row}. Error: {e}", request)
                            return super().add_view(request, form_url, extra_context)
                    messages.success(request, f'Faculty responses uploaded successfully. Total records added {records_added}', request)
                    return HttpResponseRedirect(reverse('admin:responseupload_facultyresponse_changelist'))
                else:
                    messages.error(request, "No file was chosen to upload", request)
                    return super().add_view(request, form_url, extra_context)
        return super().add_view(request, form_url, extra_context)

class CourseResponseAdmin(admin.ModelAdmin):
    list_display = ('course', 'semester')
    list_filter = ('course', 'semester')
    search_fields = ('course__name', 'general_comments')
    form = CourseResponseAdminForm
    raw_id_fields = ('faculty',)

    def response_add(self, request, obj, post_url_continue=None):
        if '_addanother' not in request.POST and '_continue' not in request.POST and '_save' in request.POST:
            messages.success(request, 'Course response uploaded successfully.')
            return HttpResponseRedirect(reverse('admin:index'))
        else:
            return super().response_add(request, obj, post_url_continue)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            course = obj.course
            subject = 'Your Course Evaluation Report Has Been Uploaded'
            # Safely handle potentially missing fields
            section = getattr(course, 'section', 'N/A')
            semester = getattr(course, 'semester', 'N/A')
            year = getattr(course, 'year', 'N/A')
            message = (
                f'Your evaluation report for Course {course.code} - {course.name} '
                f'(Section: {section}, Semester: {semester}, Year: {year}) '
                f'has been uploaded. Please login to the reporting system.\n'
                f'{request.build_absolute_uri(reverse("responseupload:login"))}'
            )
            recipient_list = [obj.faculty.email]
            from_email = settings.DEFAULT_FROM_EMAIL

            send_mail(subject, message, from_email, recipient_list)
    
    def add_view(self, request, form_url='', extra_context=None):
        if request.method == 'POST':
            form = CourseResponseAdminForm(request.POST, request.FILES)
            if form.is_valid():
                semester = form.cleaned_data['semester']
                course = form.cleaned_data['course']
                faculty_member = form.cleaned_data['faculty']
                year = form.cleaned_data['year']
                csv_file = form.cleaned_data['file']
                if csv_file:
                    if not csv_file.name.endswith('.csv'):
                        messages.error(request, 'Please upload a CSV file.', request)
                        return super().add_view(request, form_url, extra_context)
                    decoded_file = csv_file.read().decode('utf-8').splitlines()
                    reader = csv.DictReader(decoded_file)
                    records_added = 0
                    for row in reader:
                        try:
                            timestamp = row.get('Timestamp')
                            if timestamp:
                                course_response = CourseResponse(
                                    semester=semester,
                                    course=course,
                                    year=year,
                                    faculty=faculty_member,
                                    q1=row.get('1. The course provided an opportunity to develop relevant learning and competencies.'),
                                    q2=row.get('2. Textbooks/reading materials used in the course were appropriate.'),
                                    q3=row.get('3. Total time allocated for the course is appropriate to cover all the contents.'),
                                    q4=row.get('4. The contents specified in the syllabus for the course were covered.'),
                                    general_comments=row.get('General comment', ''),
                                )
                                course_response.save()
                                records_added += 1
                            else:
                                messages.error(request, "Timestamp is missing in the csv", request)
                                return super().add_view(request, form_url, extra_context)
                        except Exception as e:
                            messages.error(request, f"Error processing row: {row}. Error: {e}", request)
                            return super().add_view(request, form_url, extra_context)
                    messages.success(request, f'Course responses uploaded successfully. Total records added {records_added}', request)
                    return HttpResponseRedirect(reverse('admin:responseupload_courseresponse_changelist'))
                else:
                    messages.error(request, "No file was chosen to upload", request)
                    return super().add_view(request, form_url, extra_context)
        return super().add_view(request, form_url, extra_context)

# Other model registrations
admin.site.register(Semester)
admin.site.register(Year)

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'semester', 'year', 'program')  # Removed 'section'
    list_filter = ('semester', 'year', 'program')  # Removed 'section'
    search_fields = ('code', 'name')

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email')
    search_fields = ('first_name', 'last_name', 'email')

admin.site.register(FacultyResponse, FacultyResponseAdmin)
admin.site.register(CourseResponse, CourseResponseAdmin)