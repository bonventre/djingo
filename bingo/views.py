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
  boardsquares = Boardsquare.objects.filter(player=player).order_by('order')
  square_info = []
  for boardsquare in boardsquares:
    if boardsquare.checked:
      classname = 'checked'
    else:
      classname = 'unchecked'
    square_info.append({'text':boardsquare.square.text,'boardsquare':boardsquare.pk,'classname':classname})
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
      if totalsquares >= 25:
        squarei = random.sample(range(2,totalsquares+1),24)
      else:
        squarei = []
        for i in range(24):
          squarei.append(random.randint(2,totalsquares))
      for i in range(25):
        if i == 12:
          spot = Boardsquare(player=player,square=Square.objects.get(pk=1),checked=True,order=i)
        else:
          if i > 12:
            spot = Boardsquare(player=player,square=Square.objects.get(pk=squarei[i-1]),checked=False,order=i)
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

def deletesquare(request,squareid):
    square = get_object_or_404(Square,pk=squareid)
    boardsquares = Boardsquare.objects.filter(square=square)
    for boardsquare in boardsquares:
      board = Boardsquare.objects.filter(player=boardsquare.player)
      squareids = [square.pk]
      for spot in board:
        squareids.append(spot.square.pk)
      squareids = list(set(squareids))
      squareids.sort()
      totalsquares = Square.objects.count()
      if (totalsquares-len(squareids)) > 1:
        i = random.randint(2,totalsquares-len(squareids))
        for j in squareids:
          if i >= j:
            i += 1
      elif (totalsquares-1) > 1:
        i = random.randint(2,totalsquares-1)
        if i >= square.pk:
          i += 1
      else:
        i = 1
      boardsquare.square = Square.objects.get(pk=i)
      if i != 1:
        boardsquare.checked = False
      else:
        boardsquare.checked = True
      boardsquare.save()
    square.delete()
    return HttpResponse("Square deleted")

def deleteplayer(request,playerid):
  player = get_object_or_404(Player,pk=playerid)
  boardsquares = Boardsquare.objects.filter(player=player)
  for boardsquare in boardsquares:
    boardsquare.delete()
  player.delete()
  return HttpResponse("Player deleted")
