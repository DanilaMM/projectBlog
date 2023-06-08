from django.shortcuts import render,get_object_or_404
from django.http import Http404
from .models import Post,Comment
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from django.core.mail import send_mail
from .forms import EmailPostForm,CommentForm
from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.db.models import Count
def post_list(request,tag_slug=None): 
    post_list = Post.published.all()#экземпляр класса Post на основе всех публ.постов
    paginator = Paginator(post_list,3)#экз класса пагинатор с передаными туда постами нашими всеми публицированными и второй атрибут(3) сколько отобразить на 1 стр
    page_number = request.GET.get('page',1)
    tag = None
    if tag_slug:
        # select * from Tag where slug = tag_slug
        tag = get_object_or_404(Tag,slug=tag_slug)
        post_list = post_list.filter(tags__in=[tag])
    
    try: 
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    return render(request,'blog/post/list.html',{'posts': posts,
                                                 'tag':tag})
    
def post_detail(request, year,month,day,post):
    post = get_object_or_404(Post,
                             
                            status=Post.Status.PUBLISHED,
                            slug = post,
                            publish__year = year,
                            publish__month= month,
                            publish__day= day)
    comments = post.comments.filter(active=True)
    form = CommentForm()
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]
    return render(request,'blog/post/detail.html',{'post': post,
                                                   'comments':comments,
                                                   'form':form,
                                                   'similar_posts':similar_posts
                                                   })

def post_share(request, post_id):
    # функция сокращенного доступа для извлечения поста с id==post_id
    post = get_object_or_404(Post,
                             id=post_id,
                             status=Post.Status.PUBLISHED)
    sent = False
    # 2)
    if request.method == "POST":
        #  Когда пользователь заполняет форму и  передает ее методом POST
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # форма снова прорисовывается в  шаблоне,
            # включая переданные данные. Ошибки валидации будут отображены
            # в шаблоне.
            # в cd = dict  в котором  находятся данные из формы,
            # где ключи =  названия формы и значение = содержание
            cd = form.cleaned_data
            #непосредственно отправка письма
            post_url=request.build_absolute_uri(
                post.get_absolute_url()
            )
            subject=f"{cd['name']} recommends you read {post}"
            message= f"Mail send by {cd['email']}\n\n"\
                    f"Read {post.title} at {post_url}\n\n" \
                    f"{cd['name']}'s comments: {cd['comments']}"
            send_mail(subject, message, 'masychevvp@gmail.com',
                      [cd['to']])
            sent = True
    # 1)
    else:
        # Указанный экземпляр формы
        # будет использоваться для отображения пустой формы в шаблоне
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post': post,
                                                    'form': form,
                                                    'sent': sent})

@require_POST
def post_comment(request,post_id):
    post = get_object_or_404(Post,
                             id = post_id,
                             status = Post.Status.PUBLISHED

    )
    comment = None
    form = CommentForm(data = request.POST)
    if form.is_valid():
        comment = form.save(commit = False)
        comment.post = post
        comment.save()
    return render(request,'blog/post/comment.html',
                  {'post':post,
                   'form':form,
                   'comment':comment})

class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'

