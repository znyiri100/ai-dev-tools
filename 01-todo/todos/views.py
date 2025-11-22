from django.shortcuts import render, redirect, get_object_or_404
from .models import Todo
from django.urls import reverse

def todo_list(request):
	todos = Todo.objects.all().order_by('-created_at')
	return render(request, 'todos/home.html', {'todos': todos})

def todo_create(request):
	if request.method == 'POST':
		title = request.POST.get('title')
		description = request.POST.get('description')
		due_date = request.POST.get('due_date')
		Todo.objects.create(title=title, description=description, due_date=due_date)
		return redirect('todo_list')
	return render(request, 'todos/todo_form.html')

def todo_edit(request, pk):
	todo = get_object_or_404(Todo, pk=pk)
	if request.method == 'POST':
		todo.title = request.POST.get('title')
		todo.description = request.POST.get('description')
		todo.due_date = request.POST.get('due_date')
		todo.save()
		return redirect('todo_list')
	return render(request, 'todos/todo_form.html', {'todo': todo})

def todo_delete(request, pk):
	todo = get_object_or_404(Todo, pk=pk)
	if request.method == 'POST':
		todo.delete()
		return redirect('todo_list')
	return render(request, 'todos/todo_confirm_delete.html', {'todo': todo})

def todo_resolve(request, pk):
	todo = get_object_or_404(Todo, pk=pk)
	todo.resolved = True
	todo.save()
	return redirect('todo_list')

# Create your views here.
