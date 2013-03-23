from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse

from models import Player, Square, Boardsquare
from forms import NewPlayerForm, NewSquareForm

import random
import simplejson as json

def main(request):
  players = Player.objects.all()
  players = sorted(players,key=lambda player: player.bingos*-5000-player.score) 

  return render(request, 'bingo/index.html', {'players':players})

def playerview(request,playerid):
  player = get_object_or_404(Player,pk=int(playerid))
  boardsquares = Boardsquare.objects.filter(player=player).order_by('order')
  square_info = []
  bingo_info = []
  for boardsquare in boardsquares:
    if boardsquare.checked:
      classname = 'checked'
    else:
      classname = 'unchecked'
    if boardsquare.order < 25:
      square_info.append({'text':boardsquare.square.text,'boardsquare':boardsquare.pk,'classname':classname})
    else:
      bingo_info.append({'text':boardsquare.square.text,'boardsquare':boardsquare.pk,'classname':classname})
  return render(request, 'bingo/player.html', {'player': player,'squares': square_info,'bingosquares':bingo_info})

def newplayer(request):
  success = 0
  playerid = 0
  playername = ''
  if request.method == 'POST':
    form = NewPlayerForm(request.POST)
    if form.is_valid():
      cd = form.cleaned_data
      player = Player(name=cd['name'])
      player.save()
      squares = Square.objects.all().order_by('pk')
      if len(squares)-1 >= 24:
        squarei = random.sample(range(1,len(squares)),24)
      elif len(squares)-1 > 0:
        squarei = []
        for i in range(24):
          squarei.append(random.randint(1,len(squares)-1))
      else:
        squarei = []
        for i in range(24):
          squarei.append(0)
      for i in range(25):
        if i < 12:
          spot = Boardsquare(player=player,square=squares[squarei[i]],checked=False,order=i)
        elif i == 12:
          spot = Boardsquare(player=player,square=squares[0],checked=True,order=i)
        else:
          spot = Boardsquare(player=player,square=squares[squarei[i-1]],checked=False,order=i)
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
    data['bingos'] = player.bingos
    data['bingo'] = player.bingo
    data['score'] = player.score
    data['maxscore'] = player.maxscore
    data = json.dumps(data)
    return HttpResponse(data, mimetype='application/json')
  else:
    raise Http404

def cashinbingo(request,playerid):
  player = Player.objects.get(pk=int(playerid))
  if not player.bingo:
    raise Http404
  else:
    checked = []
    squares = Square.objects.all().order_by('pk')
    newsquares = list(Square.objects.filter(pk__gt=1).order_by('pk'))
    boardsquares = Boardsquare.objects.filter(player=player).order_by('order')
    for boardsquare in boardsquares:
      while boardsquare.square in newsquares:
        newsquares.remove(boardsquare.square)
      if boardsquare.checked:
        checked.append(1)
      else:
        checked.append(0)

    #totalsquares = Square.objects.count()
    lines = []
    for i in range(5):
      lines.append([5*i,5*i+1,5*i+2,5*i+3,5*i+4])
      lines.append([i,5+i,10+i,15+i,20+i])
    lines.append([0,6,12,18,24])
    lines.append([4,8,12,16,20])
    for line in lines:
      if all(checked[i] == 1 for i in line):
        for pos in line:
          order = boardsquares[pos].order
          if len(newsquares) > 0:
            i = random.randint(0,len(newsquares)-1)
            newsquare = Boardsquare(player=player,square=newsquares[i],order=order,checked=False)
            newsquares.remove(newsquares[i])
          elif len(squares)-1 > 0:
            i = random.randint(1,len(squares)-1)
            newsquare = Boardsquare(player=player,square=squares[i],order=order,checked=False)
          else:
            newsquare = Boardsquare(player=player,square=squares[0],order=order,checked=False)
          boardsquares[pos].order = 100
          boardsquares[pos].save()
          newsquare.save()
        break

    player.stashed_bingos += 1
    player.save()
    return HttpResponseRedirect(reverse('bingo.views.playerview',args=(playerid,)))

def deletesquare(request,squareid):
    square = get_object_or_404(Square,pk=squareid)
    squares = Square.objects.all().order_by('pk')
    boardsquares = Boardsquare.objects.filter(square=square)
    # loop over all boardsquares for the square we are deleting
    for boardsquare in boardsquares:
      # if it is part of a bingo already cashed in, just make it free parking
      if boardsquare.order > 25:
        boardsquare.square = squares[0]
      else:
        # get the other boardsquares on the board containing this one
        board = Boardsquare.objects.filter(player=boardsquare.player)
        newsquares = list(Square.objects.filter(pk__gt=1).order_by('pk'))
        for spot in board:
          while spot.square in newsquares:
            newsquares.remove(spot.square)
        if len(newsquares) > 0:
          i = random.randint(0,len(newsquares)-1)
          boardsquare.square = newsquares[i]
          newsquares.remove(newsquares[i])
        elif len(squares)-1 > 0:
          i = random.randint(1,len(squares)-1)
          boardsquare.square = squares[i]
        else:
          boardsquare.square = squares[0]
        boardsquare.checked = False
        boardsquare.save()

    square.delete()
    return HttpResponseRedirect(reverse('bingo.views.allsquares'))

def deleteplayer(request,playerid):
  player = get_object_or_404(Player,pk=playerid)
  boardsquares = Boardsquare.objects.filter(player=player)
  for boardsquare in boardsquares:
    boardsquare.delete()
  player.delete()
  return HttpResponse("Player deleted")
