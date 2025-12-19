from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, View
from django.contrib.auth.mixins import AccessMixin
from .models import Pool
from .forms import PoolForm

class Amor108MemberRequiredMixin(AccessMixin):
    """Verify that the current user is an AMOR108 member or staff."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Allow staff/admins to view pool pages
        if request.user.is_staff:
            return super().dispatch(request, *args, **kwargs)

        if not hasattr(request.user, 'amor108_member'):
            return render(request, 'shares/not_amor108_member.html')
        return super().dispatch(request, *args, **kwargs)

class PoolListView(Amor108MemberRequiredMixin, ListView):
    model = Pool
    template_name = 'pools/pool_list.html'
    context_object_name = 'pools'

class PoolDetailView(Amor108MemberRequiredMixin, DetailView):
    model = Pool
    template_name = 'pools/pool_detail.html'
    context_object_name = 'pool'

class PoolCreateView(Amor108MemberRequiredMixin, CreateView):
    model = Pool
    form_class = PoolForm
    template_name = 'pools/pool_form.html'
    success_url = reverse_lazy('pools:pool_list')

    def form_valid(self, form):
        form.instance.manager = self.request.user
        return super().form_valid(form)

class PoolJoinView(Amor108MemberRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        pool = get_object_or_404(Pool, pk=kwargs['pk'])
        if not pool.is_locked and request.user not in pool.members.all():
            pool.members.add(request.user)
            pool.check_and_lock_pool()
        return redirect('pools:pool_detail', pk=pool.pk)
