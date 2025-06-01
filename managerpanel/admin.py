# managerpanel/admin.py
from django.contrib import admin
from .models import (
    CourseAssignment, ManagerProfile, FaceToFaceSession,
    Batch, Student, Cohort
)
# Import Semester and Year if needed for filtering/display
from responseupload.models import Semester, Year, Program, Course # Ensure Program and Course are imported
from django.contrib.auth.models import User
from django import forms # Not strictly needed if not defining custom ModelForms here
from django.urls import reverse
from django.utils.html import format_html

# --- Cohort Admin ---
@admin.register(Cohort)
class CohortAdmin(admin.ModelAdmin):
    """Admin interface for managing Cohorts."""
    list_display = ('name', 'description')
    search_fields = ('name',)

# --- Manager Profile Admin (Using raw_id_fields for User selection) ---
@admin.register(ManagerProfile)
class ManagerProfileAdmin(admin.ModelAdmin):
    """Admin interface for managing Manager Profiles."""
    list_display = ('get_user_display', 'is_manager')
    list_filter = ('is_manager',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email')
    list_select_related = ('user',)

    # Use raw_id_fields for the user field for better selection UX
    raw_id_fields = ('user',)

    # Define fields to control order on add/change form.
    # 'user' will be rendered by raw_id_fields.
    fields = ('user', 'is_manager')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            # This queryset will be used by the raw_id_fields popup search.
            # Filter out users who are already managers or are superusers.
            existing_manager_user_ids = ManagerProfile.objects.values_list('user_id', flat=True)

            # If editing an existing ManagerProfile, allow the current user to be part of the queryset
            # (so it doesn't disappear from the selection if it's already set).
            obj_id = request.resolver_match.kwargs.get('object_id')
            if obj_id:
                try:
                    current_manager_profile = ManagerProfile.objects.get(pk=obj_id)
                    # Exclude all existing managers EXCEPT the one being currently edited
                    existing_manager_user_ids = existing_manager_user_ids.exclude(pk=current_manager_profile.user_id)
                except ManagerProfile.DoesNotExist:
                    pass # No current profile being edited, or it's a new one.

            kwargs["queryset"] = User.objects.exclude(
                id__in=existing_manager_user_ids
            ).exclude(
                is_superuser=True # Superusers have all permissions implicitly.
            ).order_by('username')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(description='User', ordering='user__username')
    def get_user_display(self, obj):
        if obj.user:
            link = reverse("admin:auth_user_change", args=[obj.user.id])
            return format_html('<a href="{}">{} ({})</a>', link, obj.user.get_full_name() or obj.user.username, obj.user.username)
        return "-"

    # When editing, we don't want to change the user directly.
    # The 'user' field will be handled by raw_id_fields when adding.
    # For display on the change form if needed, you might add 'get_user_display' to readonly_fields.
    # However, with raw_id_fields, the 'user' field itself provides the current value and lookup.
    # If you want the user to be non-editable after creation:
    def get_readonly_fields(self, request, obj=None):
        if obj: # if obj is not None, it means we are editing an existing object
            return ('get_user_display_readonly',) # Display a read-only version
        return () # When adding, 'user' field (via raw_id_fields) is editable

    @admin.display(description='User') # For readonly display on change form
    def get_user_display_readonly(self, obj):
         return self.get_user_display(obj)


# --- Face-to-Face Session Inline ---
class FaceToFaceSessionInline(admin.TabularInline):
    model = FaceToFaceSession
    extra = 1
    fields = ('date', 'time', 'location', 'room_number', 'support_staff_name', 'it_support_name', 'it_support_number')
    ordering = ('date', 'time')

# --- Student Inline for Batch Admin ---
class StudentInline(admin.TabularInline):
    model = Student
    extra = 0
    fields = ('student_id_link', 'first_name', 'last_name', 'email', 'degree', 'status')
    readonly_fields = ('student_id_link', 'first_name', 'last_name', 'email', 'degree', 'status')
    can_delete = False
    show_change_link = False # Using custom link
    verbose_name = "Student in Batch"
    verbose_name_plural = "Students in Batch"
    ordering = ('last_name', 'first_name')

    @admin.display(description='Student ID')
    def student_id_link(self, obj):
        link = reverse("admin:managerpanel_student_change", args=[obj.id])
        return format_html('<a href="{}">{}</a>', link, obj.student_id)

# --- Batch Admin ---
@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ('name', 'program', 'cohort', 'status', 'year', 'semester', 'student_count', 'created_at')
    list_filter = ('status', 'program', 'cohort', 'year', 'semester')
    search_fields = ('name', 'program__name', 'program__code', 'cohort__name')
    inlines = [StudentInline]
    list_select_related = ('semester', 'cohort', 'program')
    list_per_page = 20
    list_editable = ('status',)

    @admin.display(description='No. of Students', ordering='students__count')
    def student_count(self, obj):
        return obj.students.count()

# --- Student Admin ---
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'first_name', 'last_name', 'email', 'batch_link', 'degree', 'status', 'enrollment_semester')
    list_filter = ('status', 'degree', 'batch__status', 'batch__program', 'batch__cohort', 'batch', 'enrollment_semester')
    search_fields = ('student_id', 'first_name', 'last_name', 'email', 'batch__name', 'degree', 'batch__program__name', 'batch__program__code')
    list_select_related = ('batch', 'batch__cohort', 'batch__program', 'enrollment_semester')
    list_per_page = 25
    list_editable = ('status', 'degree')
    raw_id_fields = ('batch',)

    # Conditional filter_horizontal and fieldsets for 'completed_courses'
    # This assumes 'completed_courses' might not always be on the Student model.
    # If it's always there, you can remove the hasattr checks.
    def get_filter_horizontal(self, request, obj=None):
        if hasattr(Student, 'completed_courses'):
            return ('completed_courses',)
        return ()

    def get_fieldsets(self, request, obj=None):
        base_fieldsets = [
            ('Personal Info', {'fields': ('student_id', 'first_name', 'last_name', 'email', 'phone_number')}),
            ('Academic Info', {'fields': ('batch', 'degree', 'enrollment_semester', 'status')}),
        ]
        if hasattr(Student, 'completed_courses'):
            base_fieldsets.append(
                ('Completed Courses', {'classes': ('collapse',), 'fields': ('completed_courses',)})
            )
        base_fieldsets.append(('Other', {'fields': ('notes',)}))
        return tuple(base_fieldsets)


    @admin.display(description='Batch', ordering='batch__name')
    def batch_link(self, obj):
        if obj.batch:
            link = reverse("admin:managerpanel_batch_change", args=[obj.batch.id])
            return format_html('<a href="{}">{} [{}]</a>', link, obj.batch.name, obj.batch.get_status_display())
        return "-"

# --- Course Assignment Admin ---
@admin.register(CourseAssignment)
class CourseAssignmentAdmin(admin.ModelAdmin):
    list_display = ('course', 'batch', 'semester', 'year', 'modality', 'get_meeting_days_display', 'start_date', 'get_faculty_members_display')
    list_filter = ('semester', 'year', 'modality', 'course__program', 'batch__status', 'batch', 'batch__cohort', 'faculty_members')
    search_fields = ('course__code', 'course__name', 'faculty_members__username', 'faculty_members__first_name', 'faculty_members__last_name', 'batch__name')
    filter_horizontal = ('faculty_members',)
    inlines = [FaceToFaceSessionInline]
    date_hierarchy = 'start_date'
    raw_id_fields = ('course', 'batch', 'semester', 'year')
    list_select_related = ('course', 'batch', 'course__program', 'batch__cohort', 'semester', 'year')
    list_per_page = 20

    fieldsets = (
        (None, {'fields': ('course', 'batch', 'semester', 'year', 'modality', 'faculty_members')}),
        ('Schedule & Days', {'fields': ( ('start_date', 'end_date'), ('start_time', 'end_time'), ('meets_on_monday', 'meets_on_tuesday', 'meets_on_wednesday', 'meets_on_thursday'), ('meets_on_friday', 'meets_on_saturday', 'meets_on_sunday'), 'num_classes',)}),
        ('Online Details (Optional)', { 'classes': ('collapse',), 'fields': ('zoom_link', 'zoom_host_code')}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('course', 'batch', 'course__program', 'batch__cohort', 'semester', 'year').prefetch_related('faculty_members')

    @admin.display(description='Assigned Faculty')
    def get_faculty_members_display(self, obj):
        return ", ".join([f.get_full_name() or f.username for f in obj.faculty_members.all()])

    @admin.display(description='Meeting Days')
    def get_meeting_days_display(self, obj):
        return obj.get_meeting_days()