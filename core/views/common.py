from django.utils.translation import gettext as _
import calendar, csv, io, json, uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction, connection
from django.db.models import Q
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from core.models import *
from core.forms import *
from core.access import *
from core.services import *
from core.configuration import current, validate_config, learning_states


def fail(form,exc): form.add_error(None,exc)


def page(request,title,**ctx): return render(request,'core/page.html',{'title':title,**ctx})


def session_q(user): return Session.objects.filter(group__in=groups(user)).select_related('group','teacher')


def require_module(user,name):
    if not educational(user) or not current()['modules'].get(name,True): raise PermissionDenied


def generic_edit(request,form_class,title,instance=None,back='home',prepare=None):
    form=form_class(request.POST or None,request.FILES or None,instance=instance)
    if prepare: prepare(form)
    if request.method=='POST' and form.is_valid():
        try:
            with transaction.atomic(): obj=save_versioned(form,request.user)
            messages.success(request,_('Cambios guardados.')); return redirect(back)
        except ValidationError as e: fail(form,e)
    return render(request,'core/form.html',{'title':title,'form':form})
