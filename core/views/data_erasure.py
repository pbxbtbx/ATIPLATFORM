from django.contrib.auth.decorators import login_required
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.utils.translation import gettext as _
from core.models import Student, DataErasure
from core.data_erasure import (require_erasure, make_preview, load_preview, snapshot,
    erase_records, verify_files, authenticate_erasure, remaining_copy_checks)


@login_required
@never_cache
@sensitive_post_parameters('password')
def erasure_select(request):
    require_erasure(request.user)
    context = {'title': _('Retirada de datos personales'), 'students': Student.objects.order_by('name'), 'receipts': DataErasure.objects.filter(author=request.user).order_by('-created_at')[:10], 'error': ''}
    status = 200
    if request.method == 'POST':
        try:
            if request.POST.get('action') == 'erase':
                receipt = erase_records(request.user, request.POST.get('token', ''), request.POST.get('password', ''),
                    request.POST.get('confirmation', ''), request.POST.get('accept') == 'on')
                verify_files(receipt)
                return redirect('erasure_receipt', pk=receipt.pk)
            token, counts, students = make_preview(request.user, request.POST.getlist('student'))
            return render(request, 'core/erasure_preview.html', {'title': context['title'], 'token': token,
                'counts': counts, 'selected': students, 'copies': remaining_copy_checks()})
        except (ValidationError, ProtectedError) as exc:
            context['error'] = ' '.join(exc.messages) if isinstance(exc, ValidationError) else _('Hay referencias protegidas fuera de la selección. No se ha confirmado el borrado; requiere revisión.')
            status = 422
    elif request.method != 'GET':
        return HttpResponse(status=405)
    response = render(request, 'core/erasure_select.html', context, status=status)
    response['Cache-Control'] = 'private, no-store'
    return response


@login_required
@never_cache
@sensitive_post_parameters('password')
def erasure_receipt(request, pk):
    require_erasure(request.user)
    receipt = get_object_or_404(DataErasure, pk=pk, author=request.user)
    error = ''
    if request.method == 'POST':
        try:
            authenticate_erasure(request.user, request.POST.get('password', ''))
            receipt = verify_files(receipt)
        except ValidationError as exc:
            error = ' '.join(exc.messages)
    elif request.method != 'GET':
        return HttpResponse(status=405)
    response = render(request, 'core/erasure_receipt.html', {'title': _('Verificación de retirada'),
        'receipt': receipt, 'copies': remaining_copy_checks(), 'error': error,
        'passed': receipt.checks.get('database') and receipt.checks.get('files')})
    response['Cache-Control'] = 'private, no-store'
    return response
