from blog.models import Post
user = User.objects.get(username='admin')
post = Post(title='Another post',
slug='another-post',
body='Post body.',
author=user)
post.save()