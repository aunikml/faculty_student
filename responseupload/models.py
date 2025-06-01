# responseupload/models.py
from django.db import models
from django.contrib.auth.models import User

# --- Models for basic academic structure ---

class Program(models.Model):
    """ Represents an academic program (e.g., B.Sc. in CSE). """
    name = models.CharField(max_length=200, help_text="Full name of the program.")
    code = models.CharField(max_length=10, unique=True, help_text="Short unique code for the program.")

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        verbose_name = "Program"
        verbose_name_plural = "Programs"
        ordering = ['name']


# Removed CourseSection Model - Replaced by Batch in managerpanel


class Semester(models.Model):
    """ Represents an academic semester (e.g., Spring, Summer, Fall). """
    name = models.CharField(max_length=20, unique=True, help_text="Name of the semester (e.g., Spring, Summer, Fall).")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Semester"
        verbose_name_plural = "Semesters"
        ordering = ['name']


class Year(models.Model):
    """ Represents an academic year (e.g., 2024). """
    name = models.IntegerField(unique=True, help_text="Academic year (e.g., 2024).")

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = "Year"
        verbose_name_plural = "Years"
        ordering = ['-name'] # Show most recent years first


class Course(models.Model):
    """
    Represents a general course definition (e.g., CSE110 - Programming Language I).
    Specific offerings/sections with students and faculty are handled by CourseAssignment in managerpanel.
    """
    code = models.CharField(max_length=20, help_text="Standard course code (e.g., CSE110).")
    name = models.CharField(max_length=200, help_text="Full title of the course.")
    # Removed section ForeignKey
    # Kept semester/year here assuming a course definition might be tied to a specific catalog year/semester
    # If a course like 'CSE110' is always the same regardless of year/semester, you might remove these
    # and only have semester/year on the CourseAssignment.
    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        help_text="The semester this course definition is primarily associated with (e.g., catalog semester)."
        )
    year = models.ForeignKey(
        Year,
        on_delete=models.CASCADE,
        help_text="The academic year this course definition is primarily associated with (e.g., catalog year)."
        )
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        help_text="The program this course belongs to."
        )

    def __str__(self):
        # Updated string representation without section
        return f"{self.code} - {self.name} ({self.program.code} / {self.semester} {self.year})"

    class Meta:
        # Optional: Prevent exact duplicates of code/program/sem/year for a course definition
        unique_together = ('code', 'program', 'semester', 'year')
        verbose_name = "Course Definition"
        verbose_name_plural = "Course Definitions"
        ordering = ['code', 'year', 'semester']


class Faculty(models.Model):
    """
    Legacy Faculty model. NOTE: Faculty assignment is now primarily done
    using the built-in User model via CourseAssignment in managerpanel.
    This model might be redundant or used for storing additional faculty-specific
    details not present in the User model if needed.
    """
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "Faculty (Legacy Info)" # Renamed for clarity
        verbose_name_plural = "Faculty (Legacy Info)"


# --- Response Models ---

class FacultyResponse(models.Model):
    """ Stores individual student responses for a faculty evaluation. """
    # Consider removing semester/year if they are always tied to the Course
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, blank=True, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, blank=True, null=True)
    faculty = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, help_text="The faculty member being evaluated.")
    year = models.ForeignKey(Year, on_delete=models.SET_NULL, blank=True, null=True)

    # Evaluation Questions (Example Fields - Names match original CSV)
    q1 = models.CharField(max_length=50, blank=True, null=True, verbose_name="1. Organization") # Use shorter verbose names
    q2 = models.CharField(max_length=50, blank=True, null=True, verbose_name="2. Clarity")
    q3 = models.CharField(max_length=50, blank=True, null=True, verbose_name="3. Teaching Methods")
    q4 = models.CharField(max_length=50, blank=True, null=True, verbose_name="4. Learning Materials")
    q5 = models.CharField(max_length=50, blank=True, null=True, verbose_name="5. Engagement Effort")
    q6 = models.CharField(max_length=50, blank=True, null=True, verbose_name="6. Encouragement")
    q7 = models.CharField(max_length=50, blank=True, null=True, verbose_name="7. Assignment Guidance")
    q8 = models.CharField(max_length=50, blank=True, null=True, verbose_name="8. Time Management")
    general_comments = models.TextField(blank=True, null=True)

    # Add timestamp for when the response was recorded/uploaded
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"Faculty Response for {self.faculty.username} in {self.course}"

    class Meta:
        verbose_name = "Faculty Evaluation Response"
        verbose_name_plural = "Faculty Evaluation Responses"
        ordering = ['-uploaded_at', 'course', 'faculty']


class CourseResponse(models.Model):
    """ Stores individual student responses for a course evaluation. """
    # Consider removing semester/year if tied to Course
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, blank=True, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, blank=True, null=True)
    # If course evaluations are *about* a specific faculty member teaching it, keep this.
    # If they are about the course *in general* regardless of instructor, remove this.
    faculty = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, help_text="The faculty member associated with this course evaluation (if applicable).")
    year = models.ForeignKey(Year, on_delete=models.SET_NULL, blank=True, null=True)

    # Evaluation Questions (Example Fields - Names match original CSV)
    q1 = models.CharField(max_length=50, blank=True, null=True, verbose_name="1. Learning/Competencies")
    q2 = models.CharField(max_length=50, blank=True, null=True, verbose_name="2. Textbooks/Materials")
    q3 = models.CharField(max_length=50, blank=True, null=True, verbose_name="3. Time Allocation")
    q4 = models.CharField(max_length=50, blank=True, null=True, verbose_name="4. Syllabus Coverage")
    general_comments = models.TextField(blank=True, null=True)

    # Add timestamp
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        faculty_info = f" by {self.faculty.username}" if self.faculty else ""
        return f"Course Response for {self.course}{faculty_info}"

    class Meta:
        verbose_name = "Course Evaluation Response"
        verbose_name_plural = "Course Evaluation Responses"
        ordering = ['-uploaded_at', 'course', 'faculty']