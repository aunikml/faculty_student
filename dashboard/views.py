# dashboard/views.py
import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Min, Max
from collections import defaultdict
import random

# Import models from relevant apps
from managerpanel.models import Student, Batch, Program, Cohort
from managerpanel.views import is_manager # Reuse the manager check

def get_random_color(alpha=0.6):
    """Generates a random rgba color string."""
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return f'rgba({r}, {g}, {b}, {alpha})'

@login_required
@user_passes_test(is_manager, login_url='responseupload:login') # Protect the view
def analytics_dashboard(request):
    """
    Displays analytics derived from student and batch data for managers.
    """
    # --- 1. Total Students (Count & Graph Data) ---
    total_student_count = Student.objects.count()
    # Ensure students have a batch and batch has a year for meaningful aggregation
    students_by_batch_year = Student.objects.exclude(
        batch__isnull=True
    ).exclude(
        batch__year__isnull=True
    ).values('batch__year').annotate(count=Count('id')).order_by('batch__year')

    # --- 2. Students per Program (Count & Graph Data) ---
    # Ensure students have batch, program, and year
    students_per_program_year = Student.objects.exclude(
        batch__isnull=True
    ).exclude(
        batch__program__isnull=True
    ).exclude(
        batch__year__isnull=True
    ).values(
        'batch__program__id', 'batch__program__name', 'batch__year'
    ).annotate(count=Count('id')).order_by('batch__program__name', 'batch__year')

    # --- 3. On-Going Batches per Program ---
    ongoing_batches = Batch.objects.filter(
        status=Batch.STATUS_ONGOING
    ).select_related('program', 'cohort', 'semester').order_by('program__name', '-year', 'name')
    ongoing_batches_by_program = defaultdict(list)
    for batch in ongoing_batches:
        if batch.program: # Should always have a program based on model definition
            ongoing_batches_by_program[batch.program.name].append(batch)

    # --- 4. All Batches per Cohort ---
    all_batches = Batch.objects.select_related(
        'program', 'cohort', 'semester'
    ).order_by('cohort__name', '-year', 'name')
    batches_by_cohort = defaultdict(list)
    for batch in all_batches:
        if batch.cohort: # Should always have a cohort
            batches_by_cohort[batch.cohort.name].append(batch)

    # --- Prepare Data for Charts ---
    chart_data = {}
    min_year, max_year = None, None

    # Find year range from both datasets
    year_data_sets = [students_by_batch_year, students_per_program_year]
    all_years_with_data = set()
    for dataset in year_data_sets:
        for item in dataset:
            if item.get('batch__year'):
                all_years_with_data.add(item['batch__year'])

    if all_years_with_data:
        min_year = min(all_years_with_data)
        max_year = max(all_years_with_data)
        # Ensure chart_years is a list of strings for JSON compatibility if needed, though numbers are fine for chart.js
        chart_years = list(range(min_year, max_year + 1))
    else:
        chart_years = [] # No data, empty charts

    # Process Total Students Chart Data
    if chart_years:
        total_students_data = {item['batch__year']: item['count'] for item in students_by_batch_year if item.get('batch__year')}
        total_students_counts_by_year = [total_students_data.get(year, 0) for year in chart_years]
        chart_data['total_students'] = {
            'labels': [str(y) for y in chart_years], # Use string labels for Chart.js
            'data': total_students_counts_by_year,
            'label': 'Total Students by Batch Year',
        }

    # Process Per Program Chart Data
    if chart_years:
        program_chart_data = {}
        program_colors = {}
        temp_program_data = defaultdict(lambda: defaultdict(int)) # program_name -> year -> count

        for item in students_per_program_year:
            program_name = item.get('batch__program__name')
            year = item.get('batch__year')
            count = item.get('count')
            if program_name and year:
                temp_program_data[program_name][year] = count
                if program_name not in program_colors:
                     # Assign a random color - consider a predefined list for consistency
                     program_colors[program_name] = get_random_color()

        datasets_per_program = []
        for program_name, year_counts in temp_program_data.items():
            program_data_points = [year_counts.get(year, 0) for year in chart_years]
            color = program_colors.get(program_name) # Get assigned color
            datasets_per_program.append({
                'label': program_name,
                'data': program_data_points,
                'borderColor': color,
                'backgroundColor': color.replace('0.6', '0.2') if color else get_random_color(0.2), # Lighter fill
                'fill': True,
                'tension': 0.1
            })

        chart_data['students_per_program'] = {
            'labels': [str(y) for y in chart_years], # Use string labels
            'datasets': datasets_per_program
        }


    context = {
        'total_student_count': total_student_count,
        'ongoing_batches_by_program': dict(ongoing_batches_by_program), # Convert back to dict for template
        'batches_by_cohort': dict(batches_by_cohort),
        'chart_data_json': json.dumps(chart_data), # Pass chart data as JSON
    }
    return render(request, 'dashboard/analytics_dashboard.html', context)