from django.shortcuts import render
from django.utils import timezone
from django.views.generic import DetailView, ListView

from .models import Event


class EventListView(ListView):
    model = Event
    template_name = "events/events_list.html"
    context_object_name = "events"

    def get_queryset(self):
        return Event.objects.filter(
            is_published=True,
        ).order_by("start_at")


class EventDetailView(DetailView):
    model = Event
    template_name = "events/event_detail.html"
    context_object_name = "event"

    def get_queryset(self):
        return Event.objects.filter(
            is_published=True,
        )
