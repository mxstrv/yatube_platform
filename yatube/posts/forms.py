from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {'text': 'Введите текст поста',
                  'group': 'Выберите группу',
                  }
        help_texts = {'text': '* Пост не может быть пустым',
                      'group': 'Группа, к которой будет относиться пост',
                      }

    def clean_text(self):
        text = self.cleaned_data['text']
        if not text:
            raise forms.ValidationError('Пост не может быть пустым')
        return text


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)

