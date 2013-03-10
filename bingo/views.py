from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse

from models import Player, Square, Boardsquare
from forms import NewPlayerForm, NewSquareForm

import random
import simplejson as json

def main(request):
  players = Player.objects.all()
  player_info = []
  for player in players:
    score = 0
    for square in Boardsquare.objects.filter(player=player):
      if square.checked:
        score += 1
    player_info.append({'name':player.name,'id':player.pk,'score':score})

  return render(request, 'bingo/index.html', {'players':player_info})

def playerview(request,playerid):
  player = get_object_or_404(Player,pk=int(playerid))
  score = 0
  for square in Boardsquare.objects.filter(player=player):
    if square.checked:
      score += 1
  squares = Square.objects.filter(player=player).order_by('boardsquare__order')
  square_info = []
  for square in squares:
    boardsquare = Boardsquare.objects.get(player=player,square=square)
    if boardsquare.checked:
      classname = 'checked'
    else:
      classname = 'unchecked'
    square_info.append({'text':square.text,'boardsquare':boardsquare.pk,'classname':classname})
  return render(request, 'bingo/player.html', {'player': player, 'score': score, 'squares': square_info})

def newplayer(request):
  success = 0
  playerid = 0
  playername = ''
  if request.method == 'POST':
    form = NewPlayerForm(request.POST)
    if form.is_valid():
      cd = form.cleaned_data
      player = Player(name=cd['name'],bingo=False)
      player.save()
      totalsquares = Square.objects.count()
      squarei = random.sample(range(2,totalsquares+1),25)
      for i in range(25):
        if i == 12:
          spot = Boardsquare(player=player,square=Square.objects.get(pk=1),checked=True,order=i)
        else:
          spot = Boardsquare(player=player,square=Square.objects.get(pk=squarei[i]),checked=False,order=i)
        spot.save()
      playerid = player.pk
      playername = player.name
      success = 1
  else:
    form = NewPlayerForm()
  return render(request, 'bingo/newplayer.html', {'form': form, 'success': success, 'id': playerid, 'name': playername})

def newsquare(request):
  success = 0
  if request.method == 'POST':
    form = NewSquareForm(request.POST)
    if form.is_valid():
      cd = form.cleaned_data
      square = Square(text=cd['text'])
      square.save()
      success = 1
  else:
    form = NewSquareForm()
  return render(request, 'bingo/newsquare.html', {'form': form, 'success': success})

def allsquares(request):
  squares = Square.objects.filter(pk__gt=1)
  return render(request, 'bingo/squares.html', {'squares': squares})

def togglesquare(request):
  if request.method == "POST" and request.is_ajax:
    boardsquare = Boardsquare.objects.get(pk=request.POST['boardsquare'])
    if boardsquare.checked:
      boardsquare.checked = False
      data = {'checked': 0}
    else:
      boardsquare.checked = True
      data = {'checked': 1}
    boardsquare.save()
    player = Player.objects.get(pk=boardsquare.player.pk)
    score = 0
    for square in Boardsquare.objects.filter(player=player):
      if square.checked:
        score += 1
    player.checkforbingo()
    player.save()
    data['bingo'] = player.bingo
    data['score'] = score
    data = json.dumps(data)
    return HttpResponse(data, mimetype='application/json')
  else:
    raise Http404
