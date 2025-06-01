# managerpanel/models.py
from django.db import models
from django.contrib.auth.models import User
# Import necessary models from the responseupload app
from responseupload.models import Course, Semester, Program, Year

# --- Signal Imports ---
from django.db.models.signals import post_save
from django.dispatch import receiver
# --- End Signal Imports ---


# --- Cohort Model ---
class Cohort(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Name of the cohort")
    description = models.TextField(blank=True, null=True, help_text="Optional description")
    def __str__(self): return self.name
    class Meta: verbose_name = "Cohort"; verbose_name_plural = "Cohorts"; ordering = ['name']

# --- Manager Profile Model ---
class ManagerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='managerprofile', help_text="Link to User model")
    is_manager = models.BooleanField(default=True, help_text="Designates manager privileges")
    def __str__(self): return f"Manager Profile for {self.user.username}"
    class Meta: verbose_name = "Manager Profile"; verbose_name_plural = "Manager Profiles"

# --- Batch Model ---
class Batch(models.Model):
    STATUS_ONGOING = 'ongoing'; STATUS_GRADUATED = 'graduated'
    BATCH_STATUS_CHOICES = [(STATUS_ONGOING, 'On-Going'), (STATUS_GRADUATED, 'Graduated')]
    name = models.CharField(max_length=150, unique=True, help_text="Unique name for the batch")
    cohort = models.ForeignKey(Cohort, on_delete=models.PROTECT, related_name='batches', help_text="The cohort this batch belongs to")
    program = models.ForeignKey(Program, on_delete=models.PROTECT, related_name='batches', null=False, blank=False, help_text="The academic program this batch is for")
    year = models.PositiveIntegerField(help_text="Year the batch started/enrolled")
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True, help_text="Optional: Semester the batch started/enrolled")
    status = models.CharField(max_length=10, choices=BATCH_STATUS_CHOICES, default=STATUS_ONGOING, db_index=True, help_text="Current status of the batch")
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): program_code = f" ({self.program.code})" if self.program else ""; cohort_name = f" ({self.cohort.name})" if self.cohort else ""; status_display = f" [{self.get_status_display()}]"; return f"{self.name}{program_code}{cohort_name}{status_display}"
    @property
    def required_courses(self):
        if self.program: return Course.objects.filter(program=self.program).order_by('code')
        return Course.objects.none()
    class Meta: verbose_name = "Batch"; verbose_name_plural = "Batches"; ordering = ['-year', 'status', 'semester__name', 'program__code', 'cohort__name', 'name']

# --- Student Model (Includes completed_courses M2M) ---
class Student(models.Model):
    STATUS_CHOICES = [('active', 'Active'), ('inactive', 'Not Active'), ('graduated', 'Graduated'), ('dropped', 'Dropped')]
    DEGREE_CHOICES = [('pgd_med', 'P.Gd - M.ED'), ('pgd_ecd', 'P.Gd - ECD'), ('med', 'M.Ed'), ('ecd', 'ECD')]
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='students', help_text="The batch this student belongs to.")
    student_id = models.CharField(max_length=20, unique=True, help_text="Unique student ID number.")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254, unique=True, help_text="Unique student email address.")
    phone_number = models.CharField(max_length=20, blank=True, null=True, help_text="Student's contact phone number (optional).")
    degree = models.CharField(max_length=10, choices=DEGREE_CHOICES, null=True, blank=True, help_text="Student's degree program (optional).")
    enrollment_semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True, help_text="Semester the student originally enrolled (optional).")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active', help_text="Current status of the student.")
    notes = models.TextField(blank=True, null=True, help_text="Any relevant notes about the student (optional).")
    completed_courses = models.ManyToManyField(
        Course,
        related_name='completed_by_students',
        blank=True,
        verbose_name="Completed Courses",
        help_text="Courses this student has successfully completed (independent of assignments)."
    )
    def __str__(self): return f"{self.first_name} {self.last_name} ({self.student_id})"
    class Meta: verbose_name = "Student"; verbose_name_plural = "Students"; ordering = ['batch__name', 'last_name', 'first_name']

# --- Course Assignment Model ---
class CourseAssignment(models.Model):
    MODALITY_CHOICES = [('online', 'Online'), ('f2f', 'Face-to-Face'), ('blended', 'Blended')]
    course = models.ForeignKey(Course, on_delete=models.CASCADE, help_text="The course being assigned.")
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True, related_name='assignments', help_text="Optional: Link to batch.")
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True, related_name='course_assignments', help_text="Semester this assignment is offered in.")
    year = models.ForeignKey(Year, on_delete=models.SET_NULL, null=True, blank=True, related_name='course_assignments', help_text="Year this assignment is offered in.")
    modality = models.CharField(max_length=10, choices=MODALITY_CHOICES, default='online', help_text="Primary delivery mode.")
    start_date = models.DateField(help_text="Start date.")
    end_date = models.DateField(help_text="End date.")
    start_time = models.TimeField(help_text="Default start time.")
    end_time = models.TimeField(help_text="Default end time.")
    meets_on_monday = models.BooleanField(default=False, verbose_name="Mon")
    meets_on_tuesday = models.BooleanField(default=False, verbose_name="Tue")
    meets_on_wednesday = models.BooleanField(default=False, verbose_name="Wed")
    meets_on_thursday = models.BooleanField(default=False, verbose_name="Thu")
    meets_on_friday = models.BooleanField(default=False, verbose_name="Fri")
    meets_on_saturday = models.BooleanField(default=False, verbose_name="Sat")
    meets_on_sunday = models.BooleanField(default=False, verbose_name="Sun")
    num_classes = models.IntegerField(null=True, blank=True, help_text="Optional: Total classes.")
    faculty_members = models.ManyToManyField(User, related_name='assigned_courses', limit_choices_to={'is_staff': False, 'is_superuser': False}, help_text="Assigned faculty.")
    zoom_link = models.URLField(max_length=500, null=True, blank=True, help_text="Zoom link (optional).")
    zoom_host_code = models.CharField(max_length=100, null=True, blank=True, help_text="Zoom host code (optional).")
    def get_meeting_days(self): days = []; #... code ... ; return ", ".join(days) if days else "Not specified"
    def __str__(self): faculty_names = ", ".join([f.get_full_name() or f.username for f in self.faculty_members.all()]); batch_info = f" (Batch: {self.batch.name})" if self.batch else ""; sem_year_info = f" ({self.semester} {self.year})" if self.semester and self.year else ""; modality_display = self.get_modality_display() if self.modality else 'N/A'; course_code = self.course.code if self.course else 'N/A'; program_code = self.course.program.code if self.course and self.course.program else 'N/A'; return (f"{course_code} ({program_code}){batch_info}{sem_year_info} ({modality_display}) | Faculty: {faculty_names if faculty_names else 'None'}")
    class Meta: verbose_name = "Course Assignment"; verbose_name_plural = "Course Assignments"; ordering = ['-year__name', '-semester__name', '-start_date', 'course__code']

# --- Face-to-Face Session Model ---
class FaceToFaceSession(models.Model):
    course_assignment = models.ForeignKey(CourseAssignment, on_delete=models.CASCADE, related_name='f2f_sessions', help_text="Assignment this session belongs to.")
    date = models.DateField(help_text="Date of session.")
    time = models.TimeField(help_text="Time of session.")
    location = models.CharField(max_length=200, help_text="Location.")
    room_number = models.CharField(max_length=50, null=True, blank=True, help_text="Room (optional).")
    support_staff_name = models.CharField(max_length=150, null=True, blank=True, help_text="Support staff (optional).")
    it_support_name = models.CharField(max_length=150, null=True, blank=True, help_text="IT support contact (optional).")
    it_support_number = models.CharField(max_length=20, null=True, blank=True, help_text="IT support number (optional).")
    def __str__(self): time_formatted = self.time.strftime('%I:%M %p') if self.time else 'N/A'; course_code = self.course_assignment.course.code if self.course_assignment and self.course_assignment.course else 'N/A'; return (f"F2F Session: {course_code} on {self.date.strftime('%Y-%m-%d')} at {time_formatted}")
    class Meta: verbose_name = "Face-to-Face Session"; verbose_name_plural = "Face-to-Face Sessions"; ordering = ['date', 'time']; unique_together = ('course_assignment', 'date', 'time')


# --- SIGNAL RECEIVER ---
@receiver(post_save, sender=CourseAssignment)
def mark_course_completed_for_batch_students(sender, instance, created, **kwargs):
    """
    When a CourseAssignment with a batch and course is saved,
    add the course to the completed_courses list for all students in that batch.
    """
    print(f"Signal received for CourseAssignment ID: {instance.id}, Created: {created}") # Debug print
    # Check if the assignment has both a course and a batch linked
    if instance.course and instance.batch:
        course_to_complete = instance.course
        students_in_batch = Student.objects.filter(batch=instance.batch)
        student_count = students_in_batch.count() # Get count for logging

        print(f" -> Assignment links Course '{course_to_complete}' to Batch '{instance.batch}' ({student_count} students).") # Debug

        updated_count = 0
        # Iterate through students and add the course to their completed list
        for student in students_in_batch.prefetch_related('completed_courses'): # Prefetch for efficiency
            # .add() is idempotent - it won't create duplicates
            student.completed_courses.add(course_to_complete)
            updated_count += 1
            # print(f"   -> Added {course_to_complete.code} to {student}") # Verbose debug

        if updated_count > 0:
            print(f" -> Updated completed_courses for {updated_count} students in batch {instance.batch.name} with course {course_to_complete.code}.") # Summary debug
    # else:
        # print(f" -> Skipping progress update for assignment {instance.id} (missing course or batch).") # Debug

# --- END SIGNAL RECEIVER ---