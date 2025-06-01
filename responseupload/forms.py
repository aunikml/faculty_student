# responseupload/forms.py
from django import forms
# Import necessary models from this app
from .models import Program, Course, Faculty, Semester, Year
# Import PasswordChangeForm for customization
from django.contrib.auth.forms import PasswordChangeForm
# Note: User model is typically imported in views where needed, not directly in forms unless essential

# --- Forms for Creating Core Academic Components ---

class ProgramForm(forms.ModelForm):
    """Form for creating and editing Programs."""
    class Meta:
        model = Program
        fields = ['name', 'code']
        widgets = { # Add Bootstrap styling
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Bachelor of Science in Computer Science'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., BS_CSE'}),
        }
        labels = {
            'name': 'Program Name',
            'code': 'Program Code',
        }
        help_texts = {
            'name': 'Enter the full name of the academic program.',
            'code': 'Enter a short, unique code for the program.',
        }

class CourseForm(forms.ModelForm):
    """Form for creating and editing Course definitions."""
    # Ensure related fields use ordered querysets
    program = forms.ModelChoiceField(
        queryset=Program.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class':'form-select'}),
        empty_label="-- Select Program --"
    )
    semester = forms.ModelChoiceField(
        queryset=Semester.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class':'form-select'}),
        empty_label="-- Select Semester --"
    )
    year = forms.ModelChoiceField(
        queryset=Year.objects.all().order_by('-name'), # Show recent years first
        widget=forms.Select(attrs={'class':'form-select'}),
        empty_label="-- Select Year --"
    )

    class Meta:
        model = Course
        fields = ['code', 'name', 'program', 'semester', 'year'] # Removed 'section'
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., CSE110'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Programming Language I'}),
            # program, semester, year widgets handled above
        }
        labels = {
            'code': 'Course Code',
            'name': 'Course Name',
            'program': 'Program',
            'semester': 'Associated Semester',
            'year': 'Associated Year',
        }
        help_texts = {
            'code': 'Enter the standard course code.',
            'name': 'Enter the full course title.',
            'program': 'Select the program this course primarily belongs to.',
            'semester': 'Select the semester this course definition is primarily associated with (e.g., for catalog).',
            'year': 'Select the academic year this course definition is primarily associated with (e.g., for catalog).',
        }

# CourseSectionForm is removed as the model was removed

class SemesterForm(forms.ModelForm):
    """Form for creating and editing Semesters."""
    class Meta:
        model = Semester
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Spring, Fall 2024'})
        }
        labels = {'name': 'Semester Name'}
        help_texts = {'name': 'Enter the unique name for the semester.'}


class YearForm(forms.ModelForm):
    """Form for creating and editing academic Years."""
    class Meta:
        model = Year
        fields = ['name']
        widgets = {
            'name': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2024'})
        }
        labels = {'name': 'Academic Year'}
        help_texts = {'name': 'Enter the academic year (numeric).'}


class FacultyForm(forms.ModelForm):
    """
    Form for the legacy Faculty model.
    NOTE: Consider if this form is still needed if faculty are managed via the User model.
    """
    class Meta:
        model = Faculty
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'faculty@example.com'}),
        }
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email Address',
        }

# --- Password Change Form ---
class CustomPasswordChangeForm(PasswordChangeForm):
    """Custom password change form with Bootstrap styling."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to the password fields for consistent styling
        self.fields['old_password'].widget = forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter current password'})
        self.fields['new_password1'].widget = forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter new password'})
        self.fields['new_password2'].widget = forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'})

# --- Forms related to response upload were removed as per previous request ---
# If you need them back (e.g., FacultyResponseUploadForm), they would go here.