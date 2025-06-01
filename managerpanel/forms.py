# managerpanel/forms.py
from django import forms
from .models import CourseAssignment, FaceToFaceSession, Batch, Student, Cohort # Import managerpanel models
from django.contrib.auth.models import User
# Import necessary models from responseupload (ensure Course has no sem/year)
from responseupload.models import Course, Semester, Program, Year

# --- Import the Select2 widget ---
from django_select2.forms import Select2MultipleWidget

# --- Define a Custom Field for Faculty Selection ---
class FacultyMultipleChoiceField(forms.ModelMultipleChoiceField):
    """
    Custom ModelMultipleChoiceField that displays User's full name
    or username as the label.
    """
    def label_from_instance(self, user):
        # This method defines how each object in the queryset is displayed
        return user.get_full_name() or user.username

# --- Cohort Form (Optional) ---
# class CohortForm(forms.ModelForm):
#     class Meta:
#         model = Cohort
#         fields = ['name', 'description']
#         widgets = {
#             'name': forms.TextInput(attrs={'class': 'form-control'}),
#             'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
#         }

# --- Batch Form (UPDATED with Status) ---
class BatchForm(forms.ModelForm):
    """Form for creating and editing Batches."""
    cohort = forms.ModelChoiceField(
        queryset=Cohort.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class':'form-select'}),
        required=True,
        empty_label="-- Select Cohort --"
    )
    program = forms.ModelChoiceField(
        queryset=Program.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class':'form-select'}),
        required=True,
        empty_label="-- Select Program --"
    )
    semester = forms.ModelChoiceField(
        queryset=Semester.objects.all().order_by('name'),
        required=False,
        widget=forms.Select(attrs={'class':'form-select'}),
        empty_label="-- Select Semester (Optional) --"
    )
    # --- Status Field ---
    status = forms.ChoiceField(
        choices=Batch.BATCH_STATUS_CHOICES,
        widget=forms.Select(attrs={'class':'form-select'}),
        required=True # Status is required
    )
    # --- END Status Field ---

    class Meta:
        model = Batch
        fields = ['name', 'cohort', 'program', 'year', 'semester', 'status'] # Add 'status' to fields
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Spring 2024 CSE - TFB'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2024'}),
            # status widget handled above
        }
        labels = {
            'name': 'Batch Name',
            'cohort': 'Cohort Type',
            'program': 'Program',
            'year': 'Enrollment Year',
            'semester': 'Enrollment Semester',
            'status': 'Batch Status' # Add label for status
        }
        help_texts = {
            'name': 'A unique name identifying this batch.',
            'cohort': 'Select the primary cohort type for this batch.',
            'program': 'Select the academic program this batch is for.',
            'year': 'The academic year this batch primarily belongs to.',
            'semester': 'The starting semester for this batch (optional).',
            'status': 'Select the current status of the batch (e.g., On-Going, Graduated).' # Add help text
        }

# --- Student Form ---
class StudentForm(forms.ModelForm):
    """Form for manually creating and editing Students."""
    batch = forms.ModelChoiceField(
        queryset=Batch.objects.all().order_by('-year', 'status', 'semester__name', 'name'), # Add status to ordering
        widget=forms.Select(attrs={'class':'form-select'}),
        required=True
    )
    enrollment_semester = forms.ModelChoiceField(
        queryset=Semester.objects.all().order_by('name'),
        required=False,
        widget=forms.Select(attrs={'class':'form-select'}),
        empty_label="-- Select Semester --"
    )
    degree = forms.ChoiceField(
        choices=[('', '-- Select Degree --')] + Student.DEGREE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class':'form-select'})
    )
    status = forms.ChoiceField(
        choices=Student.STATUS_CHOICES,
        widget=forms.Select(attrs={'class':'form-select'}),
        required=True
    )
    class Meta:
        model = Student
        fields = ['batch', 'student_id', 'first_name', 'last_name', 'email', 'phone_number', 'degree', 'enrollment_semester', 'status', 'notes']
        widgets = {'student_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'e.g., 20101001'}), 'first_name': forms.TextInput(attrs={'class': 'form-control'}), 'last_name': forms.TextInput(attrs={'class': 'form-control'}), 'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder':'student@example.com'}), 'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}), 'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional notes'})}
        labels = {'student_id': 'Student ID', 'enrollment_semester': 'Enrollment Semester (Optional)', 'degree': 'Degree Program (Optional)'}
        help_texts = {'batch': 'Select the batch this student belongs to.', 'email': 'Must be a unique email address.', 'student_id': 'The unique university-assigned ID.', 'degree': 'Select the degree program.'}

# --- Student CSV Upload Form ---
class StudentCSVUploadForm(forms.Form):
    """Form for uploading a CSV file of students for a specific batch."""
    batch = forms.ModelChoiceField(
        queryset=Batch.objects.all().order_by('-year', 'status', 'semester__name'), # Add status to ordering
        label="Select Batch to Upload Students To",
        empty_label="-- Select Batch --",
        widget=forms.Select(attrs={'class': 'form-select mb-3'})
    )
    csv_file = forms.FileField(
        label="Upload CSV File",
        help_text="Required columns (case-insensitive): student_id, first_name, last_name, email, enrollment_semester (must match existing semester name), status (active/inactive/graduated/dropped). Optional: phone_number, degree (use keys: " + ", ".join([f"'{c[0]}'" for c in Student.DEGREE_CHOICES]) + "), notes.",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )

# --- Course Assignment Form ---
class CourseAssignmentForm(forms.ModelForm):
    """Form for creating and editing Course Assignments."""
    faculty_members = FacultyMultipleChoiceField(
        queryset=User.objects.filter(is_staff=False, is_superuser=False).order_by('last_name', 'first_name'),
        widget=Select2MultipleWidget(attrs={'data-placeholder': 'Search faculty...'}),
        required=True,
        label="Faculty Members",
    )
    course = forms.ModelChoiceField(
         queryset=Course.objects.select_related('program').all().order_by('program__code', 'code'),
         widget=forms.Select(attrs={'class': 'form-select'}),
         label="Course (Code - Name - Program)",
         empty_label="-- Select Course --"
    )
    batch = forms.ModelChoiceField(
        queryset=Batch.objects.all().order_by('-year', 'status', 'semester__name', 'name'), # Add status to ordering
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Link to Batch (Optional)",
        empty_label="-- No Specific Batch --"
    )
    semester = forms.ModelChoiceField(
        queryset=Semester.objects.all().order_by('name'),
        required=False, # Make optional initially
        widget=forms.Select(attrs={'class':'form-select'}),
        empty_label="-- Select Semester --"
    )
    year = forms.ModelChoiceField(
        queryset=Year.objects.all().order_by('-name'),
        required=False, # Make optional initially
        widget=forms.Select(attrs={'class':'form-select'}),
        empty_label="-- Select Year --"
    )
    meets_on_monday = forms.BooleanField(required=False, label="Mon", widget=forms.CheckboxInput(attrs={'class':'form-check-input ms-1'}))
    meets_on_tuesday = forms.BooleanField(required=False, label="Tue", widget=forms.CheckboxInput(attrs={'class':'form-check-input ms-1'}))
    meets_on_wednesday = forms.BooleanField(required=False, label="Wed", widget=forms.CheckboxInput(attrs={'class':'form-check-input ms-1'}))
    meets_on_thursday = forms.BooleanField(required=False, label="Thu", widget=forms.CheckboxInput(attrs={'class':'form-check-input ms-1'}))
    meets_on_friday = forms.BooleanField(required=False, label="Fri", widget=forms.CheckboxInput(attrs={'class':'form-check-input ms-1'}))
    meets_on_saturday = forms.BooleanField(required=False, label="Sat", widget=forms.CheckboxInput(attrs={'class':'form-check-input ms-1'}))
    meets_on_sunday = forms.BooleanField(required=False, label="Sun", widget=forms.CheckboxInput(attrs={'class':'form-check-input ms-1'}))
    class Meta:
        model = CourseAssignment
        fields = ['course', 'batch', 'semester', 'year', 'modality', 'start_date', 'end_date', 'start_time', 'end_time', 'meets_on_monday', 'meets_on_tuesday', 'meets_on_wednesday', 'meets_on_thursday', 'meets_on_friday', 'meets_on_saturday', 'meets_on_sunday', 'num_classes', 'faculty_members', 'zoom_link', 'zoom_host_code']
        widgets = {'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), 'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), 'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}), 'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}), 'modality': forms.Select(attrs={'class': 'form-select'}), 'num_classes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}), 'zoom_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Optional https://...'}), 'zoom_host_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'})}
        labels = {'semester': 'Semester Offered', 'year': 'Year Offered', 'num_classes': 'Number of Classes (Optional)', 'zoom_link': 'Zoom Link (Optional)', 'zoom_host_code': 'Zoom Host Code (Optional)'}
        help_texts = {'course': 'Select course definition.', 'batch': 'Optional batch link.', 'semester': 'Select semester offered.', 'year': 'Select year offered.', 'faculty_members': 'Select faculty. Type to search.'}

# --- Student Search Form ---
class StudentSearchForm(forms.Form):
    """Form for searching students with multiple criteria."""
    query = forms.CharField(
        label="Search Query", max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'ID, Email, Name...'})
    )
    program = forms.ModelChoiceField(
        label="Program", queryset=Program.objects.all().order_by('name'), required=False,
        widget=forms.Select(attrs={'class':'form-select form-select-sm'}), empty_label="All Programs"
    )
    cohort = forms.ModelChoiceField(
        label="Cohort", queryset=Cohort.objects.all().order_by('name'), required=False,
        widget=forms.Select(attrs={'class':'form-select form-select-sm'}), empty_label="All Cohorts"
    )
    degree = forms.ChoiceField(
        label="Degree", choices=[('', 'All Degrees')] + Student.DEGREE_CHOICES, required=False,
        widget=forms.Select(attrs={'class':'form-select form-select-sm'})
    )
    status = forms.ChoiceField(
        label="Status", choices=[('', 'All Statuses')] + Student.STATUS_CHOICES, required=False,
        widget=forms.Select(attrs={'class':'form-select form-select-sm'})
    )
    # Add batch status filter if needed
    # batch_status = forms.ChoiceField(
    #     label="Batch Status", choices=[('', 'All Batches')] + Batch.BATCH_STATUS_CHOICES, required=False,
    #     widget=forms.Select(attrs={'class':'form-select form-select-sm'})
    # )