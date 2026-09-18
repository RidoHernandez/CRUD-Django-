from django.shortcuts import render
from django.views import generic

from .models import Author, Book


def home(request):
	context = {
		'num_books': Book.objects.count(),
		'num_authors': Author.objects.count(),
	}
	return render(request, 'catalogo/home.html', context)


class AuthorListView(generic.ListView):
	model = Author
	template_name = 'catalogo/author_list.html'
	context_object_name = 'author_list'


class AuthorDetailView(generic.DetailView):
	model = Author
	template_name = 'catalogo/author_detail.html'
	context_object_name = 'author'


class BookListView(generic.ListView):
	model = Book
	template_name = 'catalogo/book_list.html'
	context_object_name = 'book_list'


class BookDetailView(generic.DetailView):
	model = Book
	template_name = 'catalogo/book_detail.html'
	context_object_name = 'book'
