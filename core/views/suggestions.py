"""Private suggestions by POST: same scope and filters as full search, no bulk export."""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from core.list_filters import filtered_students, filtered_groups


def suggestions(request, builder):
    query = request.POST.get('q', '').strip()
    response_data = {'items': []}
    status = 200
    if len(query) > 150:
        status = 400
    elif len(query) >= 2:
        form, queryset = builder(request.user, request.POST)
        if form.is_valid():
            response_data['items'] = [{'label': name, 'value': name} for name in queryset.values_list('name', flat=True)[:8]]
        else:
            status = 400
    response = JsonResponse(response_data, status=status)
    response['Cache-Control'] = 'private, no-store'
    response['X-Robots-Tag'] = 'noindex, nofollow'
    return response


@login_required
@require_POST
@never_cache
def student_suggestions(request):
    return suggestions(request, filtered_students)


@login_required
@require_POST
@never_cache
def group_suggestions(request):
    return suggestions(request, filtered_groups)
