from django import forms

from models import Player, Square

class NewPlayerForm(forms.ModelForm):
  class Meta:
    model = Player
    fields = ('name',)

class NewSquareForm(forms.ModelForm):
  class Meta:
    model = Square
