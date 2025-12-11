from django.http import JsonResponse
from django.views import View
from django.views.generic.list import BaseListView

from movies.models import FilmWork, Roles
from django.core.paginator import Paginator
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q


class MoviesApiMixin:
    http_method_names = ['get']

    def get_queryset(self):
        return FilmWork.objects.values(
            'id',
            'title',
            'description',
            'creation_date',
            'rating',
            'type',
        ).annotate(
            genres=ArrayAgg('genres__name', distinct=True),
            actors=ArrayAgg(
                'persons__full_name',
                filter=Q(personfilmwork__role=Roles.ACTOR),
                distinct=True,
                default=[],
            ),
            directors=ArrayAgg(
                'persons__full_name',
                filter=Q(personfilmwork__role=Roles.DIRECTOR),
                distinct=True,
                default=[],
            ),
            writers=ArrayAgg(
                'persons__full_name',
                filter=Q(personfilmwork__role=Roles.WRITER),
                distinct=True,
                default=[],
            ),
        )

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)


class MoviesListApi(MoviesApiMixin, BaseListView):
    page_size = 50

    def get_context_data(self, *, object_list=None, **kwargs):
        queryset = self.get_queryset()

        page_number = self.request.GET.get('page', 1)
        paginator = Paginator(queryset, self.page_size)

        if page_number == "first":
            page_number = 1
        elif page_number == "last":
            page_number = paginator.num_pages

        try:
            page_obj = paginator.page(page_number)
        except Exception:
            return JsonResponse({'error': 'Bad request'}, status=400)

        context = {
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'page': page_obj.number,
            'page_size': self.page_size,
            'prev': (
                page_obj.previous_page_number() if page_obj.has_previous() else None
            ),
            'next': page_obj.next_page_number() if page_obj.has_next() else None,
            'results': list(page_obj.object_list),
        }
        return context


class MoviesDetailApi(MoviesApiMixin, View):

    def get(self, request, *args, **kwargs):
        film_id = kwargs.get('pk')
        movie = self.get_queryset().filter(id=film_id).first()

        if not movie:
            return JsonResponse({'error': 'Not found'}, status=404)

        return self.render_to_response(movie)
